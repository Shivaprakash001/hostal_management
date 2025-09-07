from fastapi import APIRouter, HTTPException, Depends, status
from models.models import Student, Room, User, UserRole
from database.db import Session
from services.student_services import create_student, delete_student
from services.student_services import update_student as update_student_service
from schemas.student import StudentCreate, StudentResponse, StudentUpdate
from utils.auth import get_current_user, require_role
from typing import List

router = APIRouter(prefix="/students", tags=["students"])

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[StudentResponse])
def get_students(name: str = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Only admins can see all students
    if current_user.role != UserRole.admin:
        # If student, return only their own details
        if current_user.role == UserRole.student and current_user.student_id:
            student = db.query(Student).filter_by(id=current_user.student_id).first()
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            room_no = student.room.room_no if student.room else "Unassigned"
            user = db.query(User).filter_by(student_id=student.id).first()
            active = user.is_active if user else False
            phone_no = user.phone_no if user else None
            return [StudentResponse(id=student.id, name=student.name, room_no=room_no, active=active, phone_no=phone_no)]
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    students = db.query(Student)
    if name:
        students = students.filter(Student.name.ilike(f"%{name}%"))
    result = []
    for student in students.all():
        room_no = student.room.room_no if student.room else "Unassigned"
        user = db.query(User).filter_by(student_id=student.id).first()
        active = user.is_active if user else False
        phone_no = user.phone_no if user else None
        result.append(StudentResponse(id=student.id, name=student.name, room_no=room_no, active=active, phone_no=phone_no))
    return result  # Return the result list directly

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    room_no = student.room.room_no if student.room else "Unassigned"
    user = db.query(User).filter_by(student_id=student.id).first()
    active = user.is_active if user else False
    phone_no = user.phone_no if user else None
    return StudentResponse(id=student.id, name=student.name, room_no=room_no, active=active, phone_no=phone_no)

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def add_student(student: StudentCreate, current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
    try:
        student = create_student(student.name, db, student.room_no)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    room_no = student.room.room_no if student.room else "Unassigned"
    user = db.query(User).filter_by(student_id=student.id).first()
    active = user.is_active if user else False
    phone_no = user.phone_no if user else None
    return StudentResponse(id=student.id, name=student.name, room_no=room_no, active=active, phone_no=phone_no)

@router.delete("/{student_id}", response_model=dict)
def remove_student(student_id: int, current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
        return delete_student(student_id, db)

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student_update: StudentUpdate, current_user: User = Depends(require_role([UserRole.admin])), db: Session = Depends(get_db)):
    return update_student_service(student_id, student_update, db)

@router.put("/{student_id}/activate", response_model=dict)
def activate_student(student_id: int, db: Session = Depends(get_db)):
    # First check if student exists
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Then check if user exists for this student
    user = db.query(User).filter_by(student_id=student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found for this student")
    
    user.is_active = True
    db.commit()
    return {"message": f"Student {user.username} activated successfully"}

@router.put("/{student_id}/deactivate", response_model=dict)
def deactivate_student(student_id: int, db: Session = Depends(get_db)):
    # First check if student exists
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Then check if user exists for this student
    user = db.query(User).filter_by(student_id=student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found for this student")
    
    user.is_active = False
    db.commit()
    return {"message": f"Student {user.username} deactivated successfully"}

@router.get("/by-name/{student_name}", response_model=StudentResponse)
def get_student_by_name(student_name: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(name=student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    room_no = student.room.room_no if student.room else "Unassigned"
    user = db.query(User).filter_by(student_id=student.id).first()
    active = user.is_active if user else False
    phone_no = user.phone_no if user else None
    return StudentResponse(id=student.id, name=student.name, room_no=room_no, active=active, phone_no=phone_no)
