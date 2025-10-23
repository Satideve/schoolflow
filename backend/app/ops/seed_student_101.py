# backend/app/ops/seed_student_101.py

"""
Small helper to ensure a ClassSection + Student with id=101 exist.
Run inside the container with PYTHONPATH=/app/backend.

This script is safe to run multiple times — it will not duplicate rows
and will report what it did.
"""
from __future__ import annotations

from datetime import datetime
import sys

from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.models.student import Student
from app.models.class_section import ClassSection

DB = SessionLocal()

TARGET_STUDENT_ID = 101
TARGET_ROLL = "ROLL-101"
TARGET_NAME = "Test Student 101"

def ensure_class_section(db):
    """Create (or return) a simple default class section used for test students."""
    # Try to find any existing section first
    sec = db.query(ClassSection).order_by(ClassSection.id.asc()).first()
    if sec:
        return sec
    # create a new one
    sec = ClassSection(name="Test Section A", description="Auto-created for tests")
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec

def ensure_student(db, section: ClassSection):
    """Ensure student with TARGET_STUDENT_ID exists; otherwise create it."""
    # Prefer to find by PK first
    student = db.query(Student).filter(Student.id == TARGET_STUDENT_ID).first()
    if student:
        print(f"Student already exists: id={student.id} name={student.name} roll={student.roll_number}")
        return student

    # Also avoid duplicate roll_number if another student uses the same roll
    other = db.query(Student).filter(Student.roll_number == TARGET_ROLL).first()
    if other:
        print(f"Found existing student using same roll ({TARGET_ROLL}), returning that row (id={other.id})")
        return other

    # Create a new student with explicit id (works if DB allows explicit PK insert)
    student = Student(id=TARGET_STUDENT_ID, name=TARGET_NAME, roll_number=TARGET_ROLL, class_section_id=section.id)
    db.add(student)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # If an integrity error occurs, try to find a student by roll or id and return it
        student = db.query(Student).filter((Student.id == TARGET_STUDENT_ID) | (Student.roll_number == TARGET_ROLL)).first()
        if student:
            print("Student creation collided but found existing:", student.id, student.roll_number)
            return student
        else:
            print("Failed to create student and could not find one afterwards:", e)
            raise
    db.refresh(student)
    print(f"Created student id={student.id} name={student.name} roll={student.roll_number} class_section_id={student.class_section_id}")
    return student

def main():
    try:
        section = ensure_class_section(DB)
        _ = ensure_student(DB, section)
    finally:
        DB.close()

if __name__ == "__main__":
    main()
