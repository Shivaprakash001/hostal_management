# routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from database.db import Session, get_db
from schemas.auth import UserCreate, Token, UserResponse
from models.models import User, UserRole, Student
from utils.auth import get_current_user, require_role, create_access_token
from passlib.hash import bcrypt
from services.student_services import create_student
from typing import List


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role([UserRole.admin]))):
    print("Incoming user data:", user_data)  # Log incoming user data
    user = db.query(User).filter(User.username == user_data.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        phone_no=user_data.phone_no,
        username=user_data.username,
        role=user_data.role
    )
    new_user.password_hash = bcrypt.hash(user_data.password)
    
    if user_data.role == UserRole.student:
        # Create student with optional room assignment

        student = create_student(user_data.username, db, user_data.room_no)
        new_user.student_id = student.id
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {new_user.username} created successfully"}


# ✅ Login
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print("Login attempt:", form_data.username)  # Log the username being attempted
    user = db.query(User).filter(User.username == form_data.username).first()
    print("User from DB:", user)  # Log the user retrieved from the database
    if not user or not bcrypt.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ✅ Get current user
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "student_id": current_user.student_id
    }

@router.get("/", response_model=List[UserResponse])
def get_all_users(current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
    data = []
    users = db.query(User).all()
    for user in users:
        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "student_id": user.student_id,
            "phone_no": user.phone_no,
        }
        data.append(user_data)
    return data

@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int, current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If this is a student user, also delete the student record
    if user.student_id:
        from services.student_services import delete_student
        try:
            delete_student(user.student_id, db)
        except HTTPException:
            # If student doesn't exist, continue with user deletion
            pass
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"}
