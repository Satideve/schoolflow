# backend/app/api/v1/routers/students.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.schemas.student import StudentCreate, StudentOut
from app.repositories.student_repo import (
    create_student,
    get_student,
    list_students,
)
from app.db.session import get_db

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
