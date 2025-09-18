# backend/app/repositories/student_repo.py

from sqlalchemy.orm import Session
from app.models.student import Student
from app.schemas.student import StudentCreate

def create_student(
    db: Session, student_in: StudentCreate
) -> Student:
    db_obj = Student(**student_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_student(
    db: Session, student_id: int
) -> Student | None:
    return db.query(Student).filter(Student.id == student_id).first()

def list_students(db: Session) -> list[Student]:
    return db.query(Student).all()
