# services/payment_services.py
from models.models import Payment, Student, Room
from database.db import Session
from schemas.payments import PaymentStatus, PaymentCreate, PaymentOut

def create_payment(student_id: int, amount: float, pay_status: PaymentStatus, db: Session):
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise ValueError(f"Student with ID {student_id} does not exist")
    room_id = student.room_id
    room = db.query(Room).filter_by(id=room_id).first()
    if not room:
        raise ValueError(f"Room with ID {room_id} does not exist")
    try:
        payment = Payment(student_id=student_id, room_id=room_id, amount=amount, status=pay_status)
    except Exception as e:
        raise ValueError(f"Error creating payment: {str(e)}")
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return PaymentOut.from_orm(payment)

def update_payment_status(payment_id: int, amount: float, status: PaymentStatus, db: Session):
    payment = db.query(Payment).filter_by(id=payment_id).first()
    if not payment:
        raise ValueError(f"Payment with ID {payment_id} does not exist")
    payment.status = status
    payment.amount = amount
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
