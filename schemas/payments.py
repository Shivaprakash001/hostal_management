from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    pending = "Pending"
    paid = "Paid"
    failed = "Failed"

class PaymentMethod(str, Enum):
    cash = "Cash"
    online = "Online"

class PaymentCreate(BaseModel):
    student_id: int
    amount: float
    status: PaymentStatus = PaymentStatus.pending
    month: int
    year: int
    payment_method: PaymentMethod = PaymentMethod.cash

class PaymentCreateByName(BaseModel):
    amount: float
    status: PaymentStatus = PaymentStatus.pending
    month: int
    year: int
    payment_method: PaymentMethod = PaymentMethod.cash
    
class PaymentUpdate(BaseModel):
    amount: float | None = None
    status: PaymentStatus | None = None
    month: int | None = None
    year: int | None = None
    payment_method: PaymentMethod | None = None

class PaymentOut(BaseModel):
    id: int
    student_id: int
    room_id: int
    amount: float
    status: PaymentStatus
    date: datetime
    month: int
    year: int
    transaction_id: str
    payment_method: PaymentMethod
    receipt_generated: bool

    class Config:
        from_attributes = True

class PaymentWithStudentInfo(BaseModel):
    id: int
    student_id: int
    student_name: str
    room_id: int
    room_no: str
    amount: float
    status: PaymentStatus
    date: datetime
    month: int
    year: int
    transaction_id: str
    payment_method: PaymentMethod
    receipt_generated: bool

    class Config:
        from_attributes = True

class PaymentMarkAsPaid(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.online

class CreateOrderRequest(BaseModel):
    student_id: int
    amount: float
    month: int
    year: int

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None
    student_id: int | None = None
    month: int | None = None
    amount: float | None = None
