from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse, FileResponse
from database.db import Session
from typing import List, Optional
from schemas.payments import (
    PaymentCreate, PaymentUpdate, PaymentOut, PaymentStatus,
    PaymentCreateByName, PaymentMarkAsPaid, PaymentMethod,
    CreateOrderRequest, VerifyPaymentRequest
)
from services.payment_services import (
    create_payment, update_payment, get_payments_by_student,
    get_payments_by_room, get_payments_by_student_name,
    get_all_payments_with_student_info, get_payment_stats,
    mark_payment_as_paid, generate_payment_receipt, export_payments_to_csv
)
from models.models import Payment, Student, User, UserRole, Room
from utils.auth import get_current_user
from utils.payment_utils import generate_upi_qr
from utils.upi_config import get_upi_config
import io
import uuid
from datetime import datetime

router = APIRouter(prefix="/payments", tags=["payments"])

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# UPI Payment endpoints
@router.post('/create-order')
async def create_order(req: CreateOrderRequest, db: Session = Depends(get_db)):
    """Create a mock payment order with UPI QR code and deep link."""
    fake_order_id = f"order_{uuid.uuid4().hex[:10]}"
    payment = create_payment(
        req.student_id,
        req.amount,
        PaymentStatus.pending,
        req.month,
        req.year,
        PaymentMethod.online,
        db
    )

    # Update payment with the order ID as transaction ID for verification
    payment.transaction_id = fake_order_id
    db.commit()

    # Get UPI configuration from database
    upi_config = get_upi_config()
    upi_url, qr_bytes = generate_upi_qr(upi_config["upi_id"], upi_config["merchant_name"], req.amount, fake_order_id)

    # Return the QR code image as base64 string for frontend display
    import base64
    qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
    return {"order_id": fake_order_id, "upi_url": upi_url, "payment_id": payment.id, "qr_base64": qr_base64}

@router.get('/student-payment-info')
async def get_student_payment_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current student's payment information for auto-filling payment form."""
    if not current_user.student_id:
        raise HTTPException(status_code=400, detail="User is not associated with a student account")

    student = db.query(Student).filter_by(id=current_user.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not student.room_id:
        raise HTTPException(status_code=400, detail="Student is not assigned to any room")

    room = db.query(Room).filter_by(id=student.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Get current month and year
    from datetime import datetime
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    return {
        "student_id": student.id,
        "student_name": student.name,
        "room_no": room.room_no,
        "room_rent": room.price,
        "current_month": current_month,
        "current_year": current_year
    }

@router.post('/verify-payment')
async def verify_payment(req: VerifyPaymentRequest, db: Session = Depends(get_db)):
    """Mock payment verification - create payment record for admin verification."""
    payment = db.query(Payment).filter_by(transaction_id=req.razorpay_order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update payment with verification details but keep status as pending for admin approval
    payment.status = PaymentStatus.pending  # Keep as pending for admin verification
    payment.payment_method = PaymentMethod.online
    payment.date = datetime.utcnow()
    db.commit()
    db.refresh(payment)

    return {"status": "pending_verification", "payment_id": payment.id, "message": "Payment submitted for admin verification"}

@router.post('/admin/verify/{payment_id}')
async def admin_verify_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin endpoint to verify and approve a payment."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Payment is already verified")

    # Mark payment as paid and generate receipt
    updated = mark_payment_as_paid(payment.id, payment.payment_method, db)
    return {"status": "verified", "payment_id": updated.id, "message": "Payment verified successfully"}

@router.post('/admin/reject/{payment_id}')
async def admin_reject_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin endpoint to reject a payment."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Cannot reject a verified payment")

    payment.status = PaymentStatus.failed  # Mark as failed when rejected
    db.commit()
    db.refresh(payment)

    return {"status": "failed", "payment_id": payment.id, "message": "Payment rejected. Student needs to repay or verify the payment from their side."}

# Add a payment
@router.post("/", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def add_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    try:
        return create_payment(
            payment.student_id,
            payment.amount,
            payment.status,
            payment.month,
            payment.year,
            payment.payment_method,
            db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# New route to add payment by student name
@router.post("/by-name/{student_name}", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def add_payment_by_name(student_name: str, payment_data: PaymentCreateByName, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(name=student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        amount = payment_data.amount
        status = payment_data.status or PaymentStatus.pending
        return create_payment(
            student.id,
            amount,
            status,
            payment_data.month,
            payment_data.year,
            payment_data.payment_method,
            db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mark payment as paid (admin only)
@router.post("/{payment_id}/mark-paid", response_model=PaymentOut)
def mark_payment_as_paid_route(
    payment_id: int,
    payment_data: PaymentMarkAsPaid,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can mark payments as paid
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only administrators can mark payments as paid")

    try:
        return mark_payment_as_paid(payment_id, payment_data.payment_method, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Generate and download PDF receipt
@router.get("/{payment_id}/receipt")
def download_receipt(payment_id: int, db: Session = Depends(get_db)):
    try:
        # Get payment and student information for filename
        payment = db.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} does not exist")

        student = db.query(Student).filter_by(id=payment.student_id).first()
        if not student:
            raise ValueError("Student information not found")

        # Get month abbreviation (first 3 letters of month name)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_abbr = month_names[payment.month - 1] if 1 <= payment.month <= 12 else f"M{payment.month}"

        # Format filename: receipt_STU-0001_Oct-2024.pdf
        filename = f"receipt_STU-{student.id:04d}_{month_abbr}-{payment.year}.pdf"

        pdf_buffer = generate_payment_receipt(payment_id, db)

        # Create response with PDF content
        response = StreamingResponse(
            io.BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf"
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Export payments to CSV
@router.get("/export/csv")
def export_payments_csv(
    month: Optional[int] = Query(None, description="Filter by month (1-12)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    db: Session = Depends(get_db)
):
    try:
        csv_content = export_payments_to_csv(db, month, year, status)

        # Create response with CSV content
        response = StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=payments_export.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

# Get payment statistics for admin dashboard
@router.get("/stats/summary")
def get_payment_summary(db: Session = Depends(get_db)):
    try:
        return get_payment_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting payment stats: {str(e)}")

# Update payment details
@router.put("/{payment_id}", response_model=PaymentOut)
def update_payment_details(payment_id: int, update: PaymentUpdate, db: Session = Depends(get_db)):
    try:
        return update_payment(
            payment_id,
            db,
            amount=update.amount,
            status=update.status,
            month=update.month,
            year=update.year,
            payment_method=update.payment_method
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get payments by student name
@router.get("/student/{name}", response_model=List[PaymentOut])
def payments_of_student(name: str, db: Session = Depends(get_db)):
    try:
        return get_payments_by_student_name(name, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get payments by student ID
@router.get("/student/id/{student_id}", response_model=List[PaymentOut])
def payments_of_student_by_id(student_id: int, db: Session = Depends(get_db)):
    try:
        return get_payments_by_student(student_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get payments by room
@router.get("/room/{room_id}", response_model=List[PaymentOut])
def payments_of_room(room_id: int, db: Session = Depends(get_db)):
    try:
        return get_payments_by_room(room_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get all payments with optional filters
@router.get("/", response_model=List[dict])
def get_all_payments(
    month: Optional[int] = Query(None, description="Filter by month (1-12)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can see all payments
    if current_user.role != UserRole.admin:
        # If student, return only their own payments
        if current_user.role == UserRole.student and current_user.student_id:
            try:
                payments = get_payments_by_student(current_user.student_id, db)
                # Convert PaymentOut objects to dicts for response validation
                return [payment.dict() if hasattr(payment, "dict") else payment for payment in payments]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting payments: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    try:
        payments = get_all_payments_with_student_info(db, month, year, status)
        # Convert PaymentOut objects to dicts for response validation
        return [payment.dict() if hasattr(payment, "dict") else payment for payment in payments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting payments: {str(e)}")

# Get payments with student names (legacy endpoint)
@router.get("/with-student-names/", response_model=List[dict])
def get_payments_with_student_names(db: Session = Depends(get_db)):
    payments = db.query(Payment, Student.name).join(Student, Payment.student_id == Student.id).all()
    result = []
    for payment, student_name in payments:
        payment_dict = PaymentOut.from_orm(payment).dict()
        payment_dict["student_name"] = student_name
        result.append(payment_dict)
    return result

# Get all payments with student information (for admin dashboard)
@router.get("/all-with-students", response_model=List[dict])
def get_all_payments_with_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payments with student and room information for admin dashboard."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        payments = get_all_payments_with_student_info(db)
        # Convert PaymentOut objects to dicts for response validation
        return [payment.dict() if hasattr(payment, "dict") else payment for payment in payments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting payments: {str(e)}")

@router.delete("/{payment_id}", response_model=dict)
def remove_payment(payment_id: int, db: Session = Depends(get_db)):
    from services.payment_services import delete_payment
    try:
        return delete_payment(payment_id, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
