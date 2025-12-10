# backend/app/api/v1/routers/students.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.student import Student
from app.models.user import User
from app.repositories.student_repo import (
    create_student,
    get_student,
    list_students,
)
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.schemas.user import UserOut, StudentPortalUserCreate
from app.api.dependencies.auth import require_roles
from app.api.v1.routers.auth import get_password_hash

router = APIRouter(
    prefix="/api/v1/students",
    tags=["students"],
)


def _to_student_out(student: Student) -> StudentOut:
    """
    Map a Student ORM instance to StudentOut, including portal_user_email
    from the linked User (if any).
    """
    out = StudentOut.model_validate(student, from_attributes=True)
    if getattr(student, "user", None) is not None and student.user.email:
        out = out.model_copy(update={"portal_user_email": student.user.email})
    return out


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student_endpoint(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
):
    student = create_student(db, student_in)
    return _to_student_out(student)


@router.get("/", response_model=List[StudentOut])
def read_students(db: Session = Depends(get_db)):
    students = list_students(db)
    return [_to_student_out(s) for s in students]


@router.get("/{student_id}", response_model=StudentOut)
def read_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _to_student_out(student)


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
    return _to_student_out(student)


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


# --------------------------------------------------------------------
# NEW: Admin-only endpoint to create a portal user for a student
# --------------------------------------------------------------------
@router.post(
    "/{student_id}/portal-user",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin", "clerk", "accountant"))],
)
def create_portal_user_for_student(
    student_id: int,
    payload: StudentPortalUserCreate,
    db: Session = Depends(get_db),
):
    """
    Create and link a portal user account for an existing student.

    Rules:
      - Student must exist.
      - That student must not already have a linked user.
      - Email must be unique (no existing user with same email).
      - Role is always forced to "student".
    """
    # 1) Ensure student exists
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # 2) Ensure no user already linked to this student
    existing_for_student = (
        db.query(User)
        .filter(User.student_id == student_id)
        .first()
    )
    if existing_for_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This student already has a linked user account",
        )

    # 3) Ensure email is not already taken
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # 4) Hash password and create user with role="student"
    hashed_pw = get_password_hash(payload.password)

    user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        role="student",
        is_active=True,
        student_id=student_id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
