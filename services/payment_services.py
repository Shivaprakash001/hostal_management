# services/payment_services.py
from sqlalchemy import func
from models.models import Payment, Student, Room
from database.db import Session
from schemas.payments import PaymentStatus, PaymentCreate, PaymentOut, PaymentMethod
import uuid
from datetime import datetime
import csv
from io import StringIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def generate_transaction_id() -> str:
    """Generate a unique transaction ID."""
    return f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8].upper()}"

def generate_receipt_id() -> str:
    """Generate a unique receipt ID."""
    return f"RCPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8].upper()}"

def create_payment(student_id: int, amount: float, pay_status: PaymentStatus, month: int, year: int, payment_method: PaymentMethod, db: Session):
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise ValueError(f"Student with ID {student_id} does not exist")
    
    room_id = student.room_id
    if not room_id:
        raise ValueError(f"Student {student.name} is not assigned to any room")
    
    room = db.query(Room).filter_by(id=room_id).first()
    if not room:
        raise ValueError(f"Room with ID {room_id} does not exist")
    
    # Validate month and year
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    if year < 2020 or year > 2030:
        raise ValueError("Year must be between 2020 and 2030")
    
    try:
        payment = Payment(
            student_id=student_id, 
            room_id=room_id, 
            amount=amount, 
            status=pay_status,
            month=month,
            year=year,
            transaction_id=generate_transaction_id(),
            payment_method=payment_method,
            receipt_generated=False
        )
    except Exception as e:
        raise ValueError(f"Error creating payment: {str(e)}")
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return PaymentOut.from_orm(payment)

def update_payment(payment_id: int, db: Session, amount: float | None = None, 
                  status: PaymentStatus | None = None, month: int | None = None, 
                  year: int | None = None, payment_method: PaymentMethod | None = None):
    """Update payment details with optional fields."""
    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise ValueError(f"Payment with ID {payment_id} does not exist")
    
    # Update only the fields that are provided (not None)
    if amount is not None:
        payment.amount = amount
    if status is not None:
        payment.status = status
    if month is not None:
        # Validate month
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        payment.month = month
    if year is not None:
        # Validate year
        if year < 2020 or year > 2030:
            raise ValueError("Year must be between 2020 and 2030")
        payment.year = year
    if payment_method is not None:
        payment.payment_method = payment_method
    
    db.commit()
    db.refresh(payment)
    return payment

def get_payments_by_student(student_id: int, db: Session):
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise ValueError(f"Student with ID {student_id} does not exist")
    return [PaymentOut.from_orm(payment) for payment in student.payments]

def get_payments_by_student_name(name: str, db: Session):
    student = db.query(Student).filter_by(name=name).first()
    if not student:
        raise ValueError(f"Student {name} does not exist")
    return [PaymentOut.from_orm(payment) for payment in student.payments]

def get_payments_by_room(room_id: int, db: Session):
    room = db.query(Room).filter_by(id=room_id).first()
    if not room:
        raise ValueError(f"Room with ID {room_id} does not exist")
    return room.payments

def delete_payment(payment_id: int, db: Session):
    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise ValueError(f"Payment with ID {payment_id} does not exist")
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully", "deleted_payment": {"id": payment_id}}

def get_all_payments_with_student_info(db: Session, month: int = None, year: int = None, status: PaymentStatus = None):
    """Get all payments with student and room information, optionally filtered."""
    query = db.query(Payment, Student.name, Room.room_no).join(
        Student, Payment.student_id == Student.id
    ).join(
        Room, Payment.room_id == Room.id
    )
    
    if month:
        query = query.filter(Payment.month == month)
    if year:
        query = query.filter(Payment.year == year)
    if status:
        query = query.filter(Payment.status == status)
    
    results = query.all()
    payments_with_info = []
    
    for payment, student_name, room_no in results:
        payment_dict = PaymentOut.from_orm(payment).dict()
        payment_dict["student_name"] = student_name
        payment_dict["room_no"] = room_no
        payments_with_info.append(payment_dict)
    
    return payments_with_info

def get_payment_stats(db: Session):
    """Get payment statistics for admin dashboard."""
    total_payments = db.query(Payment).count()
    paid_payments = db.query(Payment).filter(Payment.status == PaymentStatus.paid).count()
    pending_payments = db.query(Payment).filter(Payment.status == PaymentStatus.pending).count()
    
    total_collected = db.query(Payment).filter(Payment.status == PaymentStatus.paid).with_entities(
        func.sum(Payment.amount)
    ).scalar() or 0
    
    total_pending = db.query(Payment).filter(Payment.status == PaymentStatus.pending).with_entities(
        func.sum(Payment.amount)
    ).scalar() or 0
    
    return {
        "total_payments": total_payments,
        "paid_payments": paid_payments,
        "pending_payments": pending_payments,
        "total_collected": total_collected,
        "total_pending": total_pending
    }

def mark_payment_as_paid(payment_id: int, payment_method: PaymentMethod, db: Session):
    """Mark a payment as paid and generate receipt."""
    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise ValueError(f"Payment with ID {payment_id} does not exist")
    
    if payment.status == PaymentStatus.paid:
        raise ValueError("Payment is already marked as paid")
    
    payment.status = PaymentStatus.paid
    payment.payment_method = payment_method
    payment.receipt_generated = True
    payment.date = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    return PaymentOut.from_orm(payment)

def generate_payment_receipt(payment_id: int, db: Session):
    """Generate a professional PDF receipt for a payment."""
    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise ValueError(f"Payment with ID {payment_id} does not exist")
    
    student = db.query(Student).filter_by(id=payment.student_id).first()
    room = db.query(Room).filter_by(id=payment.room_id).first()
    
    if not student or not room:
        raise ValueError("Student or room information not found")
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Custom styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=22,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        'ReceiptSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # Header style
    header_style = ParagraphStyle(
        'ReceiptHeader',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    # Normal style
    normal_style = ParagraphStyle(
        'ReceiptNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Footer style
    footer_style = ParagraphStyle(
        'ReceiptFooter',
        parent=styles['Normal'],
        fontSize=8,
        spaceBefore=20,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    
    # Header with logo and address
    header_elements = [
        Paragraph("HOSTEL MANAGEMENT SYSTEM", title_style),
        Paragraph("OFFICIAL PAYMENT RECEIPT", subtitle_style),
        Spacer(1, 10),
        Paragraph("123 Hostel Street, Campus Area", normal_style),
        Paragraph("City, State - 123456", normal_style),
        Paragraph("Phone: +91 98765 43210 | Email: hostel@example.com", normal_style),
        Spacer(1, 20)
    ]
    elements.extend(header_elements)
    
    # Generate unique receipt ID
    receipt_id = generate_receipt_id()
    
    # Receipt details in a more organized table
    receipt_data = [
        # Transaction Details
        ["TRANSACTION DETAILS", ""],
        ["Receipt Number:", receipt_id],
        ["Transaction ID:", payment.transaction_id],
        ["Date of Payment:", payment.date.strftime("%B %d, %Y") if payment.date else "N/A"],
        ["Time of Payment:", f"{payment.date.strftime('%I:%M %p')} UTC" if payment.date else "N/A"],
        ["", ""],
        
        # Student Information
        ["STUDENT INFORMATION", ""],
        ["Student Name:", student.name],
        ["Student ID:", f"STU-{student.id:04d}"],
        ["Room Number:", f"Room {room.room_no}"],
        ["", ""],
        
        # Payment Information
        ["PAYMENT INFORMATION", ""],
        ["Month:", f"{get_month_name(payment.month)} {payment.year}"],
        ["Amount Paid:", f"Rs. {payment.amount:,.2f}"],
        ["Payment Method:", payment.payment_method.value.upper()],
        ["Payment Status:", payment.status.value.upper()],
        ["", ""],
        
        # Financial Details
        ["FINANCIAL DETAILS", ""],
        ["Base Amount:", f"Rs. {payment.amount:,.2f}"],
        ["Tax/GST:", "Rs. 0.00"],
        ["Total Amount:", f"Rs. {payment.amount:,.2f}"],
        ["Amount in Words:", amount_to_words(payment.amount)]
    ]
    
    # Create table with better styling
    table = Table(receipt_data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        # Header rows
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#2c3e50')),
        ('BACKGROUND', (0, 12), (-1, 12), colors.HexColor('#2c3e50')),
        ('BACKGROUND', (0, 18), (-1, 18), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 6), (-1, 6), colors.whitesmoke),
        ('TEXTCOLOR', (0, 12), (-1, 12), colors.whitesmoke),
        ('TEXTCOLOR', (0, 18), (-1, 18), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('FONTNAME', (0, 12), (-1, 12), 'Helvetica-Bold'),
        ('FONTNAME', (0, 18), (-1, 18), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 6), (-1, 6), 11),
        ('FONTSIZE', (0, 12), (-1, 12), 11),
        ('FONTSIZE', (0, 18), (-1, 18), 11),
        
        # Regular rows
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Payment confirmation message
    confirmation_text = f"""
    This document serves as an official receipt for the payment made by {student.name} 
    for hostel accommodation during {get_month_name(payment.month)} {payment.year}. 
    The payment has been successfully processed and recorded in our system.
    """
    elements.append(Paragraph(confirmation_text, normal_style))
    elements.append(Spacer(1, 15))
    
    # Signature area with better formatting
    signature_data = [
        ["", "", ""],
        ["_________________________", "_________________________", "_________________________"],
        ["Student Signature", "Warden Signature", "Cashier/System"],
        ["", "", ""]
    ]
    
    signature_table = Table(signature_data, colWidths=[2.5*inch, 2.5*inch, 2*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 1), (-1, 1), 15),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 5),
    ]))
    
    elements.append(signature_table)
    elements.append(Spacer(1, 15))
    
    # Footer
    footer_elements = [
        Paragraph("Thank you for your payment!", footer_style),
        Paragraph("This is a computer-generated receipt. No physical signature required.", footer_style),
        Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} (Local Time)", footer_style),
        Paragraph("For any queries, please contact hostel administration", footer_style)
    ]
    elements.extend(footer_elements)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def get_month_name(month):
    """Get month name from month number."""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return months[month - 1] if 1 <= month <= 12 else f"Month {month}"

def amount_to_words(amount):
    """Convert amount to words (basic implementation)."""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", 
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    if amount == 0:
        return "Zero Rupees Only"
    
    # Handle rupees part
    rupees = int(amount)
    paise = round((amount - rupees) * 100)
    
    def convert_less_than_thousand(n):
        if n == 0:
            return ""
        elif n < 10:
            return units[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
        else:
            # For numbers >= 100, use recursive conversion
            hundreds = n // 100
            remainder = n % 100
            if hundreds < 10:
                result = units[hundreds] + " Hundred"
            else:
                # For numbers >= 1000, we need a more complex implementation
                result = str(n)  # Fallback to number for large amounts
            if remainder > 0:
                result += " and " + convert_less_than_thousand(remainder)
            return result
    
    result = convert_less_than_thousand(rupees)
    
    # Add paise if any
    if paise > 0:
        result += " and " + convert_less_than_thousand(paise) + " Paise"
    
    return result + " Only"

def export_payments_to_csv(db: Session, month: int = None, year: int = None, status: PaymentStatus = None):
    """Export payments data to CSV format."""
    payments = get_all_payments_with_student_info(db, month, year, status)
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Student ID', 'Student Name', 'Room Number', 'Month', 'Year', 
        'Amount', 'Transaction ID', 'Date', 'Status', 'Payment Method'
    ])
    
    # Write data
    for payment in payments:
        writer.writerow([
            payment['student_id'],
            payment['student_name'],
            payment['room_no'],
            payment['month'],
            payment['year'],
            payment['amount'],
            payment['transaction_id'],
            payment['date'].strftime('%Y-%m-%d %H:%M:%S'),
            payment['status'],
            payment['payment_method']
        ])
    
    output.seek(0)
    return output.getvalue()
