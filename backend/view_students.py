from database.db import session
from models.student import Student

def view_students():
    students=session.query(Student).all()
    if not students:
        print("No students found.")
        return
    
    print("List of Student:")
    for s in students:
        print(f"Name: {s.name}, ID: {s.student_id}, Room: {s.room_no}")