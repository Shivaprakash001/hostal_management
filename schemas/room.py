from pydantic import BaseModel
from typing import List, TYPE_CHECKING

# Avoid circular import by only importing during type checking
if TYPE_CHECKING:
    from schemas.student import StudentResponse

# ---------- Room Schemas ----------
class RoomCreate(BaseModel):
    room_no: str
    capacity: int
    price: float

class RoomOut(BaseModel):
    id: int
    room_no: str
    capacity: int
    price: float
    payment_status: str
    total_payments: float

    class Config:
        from_attributes = True

class RoomWithStudents(RoomOut):
    students: List["StudentResponse"] = []  # forward reference as string

    class Config:
        from_attributes = True

# Minimal schema for students inside a room
class StudentResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Delete room schema
class DeleteRoom(BaseModel):
    room_no: str

class UpdateRoom(BaseModel):
    new_room_no: str | None = None
    price: float | None = None
    capacity: int | None = None



# Fix forward references
RoomWithStudents.model_rebuild()
