from database.db import session
from models.student import Student
import uuid

def add_student(name,room_no):
    student=Student(
        name=name,
        student_id=str(uuid.uuid4())[:8],
        room_no=room_no
    )
    session.add(student)
    session.commit()
    print(f"Student {name} added successfully!")