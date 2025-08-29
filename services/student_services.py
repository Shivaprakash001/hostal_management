# services/student_services.py
from models.models import Student, Room
from database.db import Session
from typing import Optional
from fastapi import HTTPException
from schemas.student import StudentResponse, StudentUpdate
from models.models import User

def create_student(name: str, db: Session, room_no: Optional[str]=None) -> Student:
    try:
        check_student = db.query(Student).filter_by(name=name).first()
        if check_student:
            raise HTTPException(status_code=400,detail=f"Student {name} already exists")
        student = Student(name=name)
        if room_no:
            room = db.query(Room).filter_by(room_no=room_no).first()
            if not room:
                raise HTTPException(status_code=400,detail=f"Room {room_no} does not exist")
            count = db.query(Student).filter_by(room_id=room.id).count()
            if count >= room.capacity:
                raise HTTPException(status_code=400,detail=f"Room {room_no} is at full capacity")
            student.room_id = room.id
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def delete_student(student_id: int, db: Session):
    try:
        student = db.query(Student).filter_by(id=student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student with ID {student_id} does not exist")

        # Delete associated user account if it exists
        user = db.query(User).filter_by(student_id=student_id).first()
        if user:
            db.delete(user)

        db.delete(student)
        db.commit()
        return {"message": "Student and associated user account deleted successfully", "deleted_student": {"id": student_id}}

    except Exception:
        db.rollback()
        raise

def update_student(student_id: int, student_update: StudentUpdate, db: Session) -> StudentResponse:
    try:

        student = db.query(Student).filter_by(id=student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # ✅ Update name
        if student_update.name:
            student.name = student_update.name

        # ✅ Update room assignment
        if student_update.room_no is not None:
            if student_update.room_no == "":
                # Remove room assignment
                student.room_id = None
            else:
                room = db.query(Room).filter_by(room_no=student_update.room_no).first()
                if not room:
                    raise HTTPException(status_code=400, detail="Room does not exist")
                count = db.query(Student).filter_by(room_id=room.id).count()
                if count >= room.capacity:
                    raise HTTPException(status_code=400, detail="Room is at full capacity")
                student.room_id = room.id

        # ✅ Update phone number on related User
        if student_update.phone_no is not None:
            user = db.query(User).filter_by(student_id=student.id).first()
            if user:
                user.phone_no = student_update.phone_no

        # Commit changes
        db.commit()
        db.refresh(student)

        # Build response
        room_no = student.room.room_no if student.room else "Unassigned"
        user = db.query(User).filter_by(student_id=student.id).first()
        active = user.is_active if user else False
        phone_no = user.phone_no if user else None

        return StudentResponse(
            id=student.id,
            name=student.name,
            room_no=room_no,
            active=active,
            phone_no=phone_no
        ).dict()  # Ensure it returns a dictionary for proper serialization
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))