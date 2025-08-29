# models/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database.db import Base
import enum
from datetime import datetime
from schemas.payments import PaymentStatus
from sqlalchemy import Boolean
from passlib.hash import bcrypt


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    room_no = Column(String(20), unique=True, nullable=False)
    capacity = Column(Integer, default=4, nullable=False)
    price = Column(Float, default=0, nullable=False)
    payment_status=Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    total_payments=Column(Float, default=0, nullable=False)

    # Relationships
    students = relationship("Student", back_populates="room", cascade="all, delete")
    payments = relationship("Payment", back_populates="room", cascade="all, delete")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"))  # Optional, can be set to None if not assigned
    # Relationships
    room = relationship("Room", back_populates="students")
    payments = relationship("Payment", back_populates="student", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"))
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)

    # Relationships
    student = relationship("Student", back_populates="payments")
    room = relationship("Room", back_populates="payments")

class UserRole(enum.Enum):
    admin = "Admin"
    agent = "Agent"
    student = "Student"
    chef = "Chef"
    worker = "Worker"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    phone_no = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    # Optional FK: link student accounts with student table
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)

    student = relationship("Student",backref="user", uselist=False)

    # helper methods
    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)

    def set_password(self, password: str):
        self.password_hash = bcrypt.hash(password)
