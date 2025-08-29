from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Student(Base):
    __tablename__="students"

    id=Column(Integer, primary_key=True)
    name=Column(String,nullable=False)
    student_id= Column(String,unique=True,nullable=False)
    room_no=Column(String)

    def __repr__(self):
        return f"<Student(name={self.name}, id={self.student_id}, room={self.room_no})>"