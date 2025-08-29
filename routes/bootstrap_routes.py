# routes/bootstrap_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import User, UserRole
from schemas.auth import UserCreate
from passlib.hash import bcrypt

router = APIRouter(prefix="/bootstrap", tags=["Bootstrap"])

@router.post("/admin")
def bootstrap_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if any admin already exists
    existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
    if existing_admin:
        raise HTTPException(status_code=403, detail="Admin already exists. This route is disabled.")

    # Create the very first admin
    new_admin = User(
        username=user_data.username,
        role=UserRole.admin,
        password_hash=bcrypt.hash(user_data.password)
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"message": f"Bootstrap admin '{new_admin.username}' created successfully"}
