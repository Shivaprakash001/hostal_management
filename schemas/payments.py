from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    pending = "Pending"
    paid = "Paid"
    failed = "Failed"

class PaymentCreate(BaseModel):
    student_id: int
    amount: float
    status: PaymentStatus = PaymentStatus.pending

class PaymentCreateByName(BaseModel):
    student_name: str
    amount: float
    status: PaymentStatus = PaymentStatus.pending
    
class PaymentUpdate(BaseModel):
    amount: float | None = None
    status: PaymentStatus | None = None

class PaymentOut(BaseModel):
    id: int
    student_id: int
    room_id: int
    amount: float
    status: PaymentStatus
    date: datetime

    class Config:
        from_attributes = True
