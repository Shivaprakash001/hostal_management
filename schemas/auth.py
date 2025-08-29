# schemas/auth.py
from pydantic import BaseModel
from models.models import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.student
    room_no: str | None = None
    phone_no: int | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: str | None = None
    role: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    student_id: int | None = None
    phone_no: int | None = None

    class Config:
        from_attributes = True
