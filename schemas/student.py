from pydantic import BaseModel
from typing import Optional

class StudentCreate(BaseModel):
    name: str
    room_no: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    name: str
    room_no: Optional[str] = None
    active: bool = False
    phone_no: Optional[int] = None
    
    class Config:
        from_attributes = True

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    room_no: Optional[str] = None
    phone_no: Optional[int] = None
    class Config:
        from_attributes = True