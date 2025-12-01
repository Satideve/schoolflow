# backend/app/api/v1/routers/students.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.student import Student
from app.repositories.student_repo import (
    create_student,
    get_student,
    list_students,
)
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(
    prefix="/api/v1/students",
    tags=["students"],
)


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student_endpoint(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
):
    return create_student(db, student_in)


@router.get("/", response_model=List[StudentOut])
def read_students(db: Session = Depends(get_db)):
    return list_students(db)


@router.get("/{student_id}", response_model=StudentOut)
def read_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.patch("/{student_id}", response_model=StudentOut)
def update_student_endpoint(
    student_id: int,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student_in.name is not None:
        student.name = student_in.name
    if student_in.roll_number is not None:
        student.roll_number = student_in.roll_number
    if student_in.class_section_id is not None:
        student.class_section_id = student_in.class_section_id

    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_endpoint(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        db.delete(student)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Likely invoices, fee assignments, etc. are referencing this student
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete student because it is referenced by other records.",
        )
    return None
