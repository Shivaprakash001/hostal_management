from fastapi import APIRouter, HTTPException, Depends, status
from database.db import Session
from typing import List
from schemas.payments import PaymentCreate, PaymentUpdate, PaymentOut, PaymentStatus, PaymentCreateByName
from services.payment_services import create_payment, update_payment_status, get_payments_by_student, get_payments_by_room, get_payments_by_student_name
from models.models import Payment, Student

router = APIRouter(prefix="/payments", tags=["payments"])

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# Add a payment
@router.post("/", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def add_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    try:
        return create_payment(payment.student_id, payment.amount, payment.status, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# New route to add payment by student name
@router.post("/by-name/{student_name}", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def add_payment_by_name(payment_data: PaymentCreateByName, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(name=payment_data.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        amount = payment_data.amount
        status = payment_data.status or PaymentStatus.pending
        return create_payment(student.id, amount, status, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update payment status
@router.put("/{payment_id}", response_model=PaymentOut)
def change_payment_status(payment_id: int, update: PaymentUpdate, db: Session = Depends(get_db)):
    try:
        return update_payment_status(payment_id, update.amount, update.status, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get payments by student
@router.get("/student/{name}", response_model=List[PaymentOut])
def payments_of_student(name: str, db: Session = Depends(get_db)):
    try:
        return get_payments_by_student_name(name, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Get payments by room
@router.get("/room/{room_id}", response_model=List[PaymentOut])
def payments_of_room(room_id: int, db: Session = Depends(get_db)):
    try:
        return get_payments_by_room(room_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=List[PaymentOut])
def get_all_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    return [PaymentOut.from_orm(payment) for payment in payments]

# Get payments with student names
@router.get("/with-student-names/", response_model=List[dict])
def get_payments_with_student_names(db: Session = Depends(get_db)):
    payments = db.query(Payment, Student.name).join(Student, Payment.student_id == Student.id).all()
    result = []
    for payment, student_name in payments:
        payment_dict = PaymentOut.from_orm(payment).dict()
        payment_dict["student_name"] = student_name
        result.append(payment_dict)
    return result

@router.delete("/{payment_id}", response_model=dict)
def remove_payment(payment_id: int, db: Session = Depends(get_db)):
    from services.payment_services import delete_payment
    try:
        return delete_payment(payment_id, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
