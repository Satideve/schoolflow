# backend/tests/seed_fixtures.py

"""
Test fixtures used by fee-related endpoint tests.

Provides:
- seed_student: creates a ClassSection and a Student (committed to the test DB).
- seed_fee_plan: creates a FeePlan and a FeeAssignment linking the given student to the plan.

Both fixtures use the existing `db_session` fixture from conftest.py so they run inside
the same transactional/session environment the app/test client uses.
"""
import uuid
import pytest


@pytest.fixture
def seed_student(db_session):
    """
    Create and return a Student (and its ClassSection) in the test DB.
    """
    from app.models.class_section import ClassSection
    from app.models.student import Student

    # Create a class section first (required FK)
    section = ClassSection(name="Test Section", academic_year="2025-26")
    db_session.add(section)
    db_session.commit()
    db_session.refresh(section)

    # Create student with a unique roll number
    student = Student(
        name="Seed Student",
        roll_number=f"RN-{uuid.uuid4().hex[:8]}",
        class_section_id=section.id,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    return student


@pytest.fixture
def seed_fee_plan(db_session, seed_student):
    """
    Create and return a FeePlan, and attach it to the provided seed_student via FeeAssignment.
    The fixture depends on seed_student so the assignment can reference the created student.
    """
    from app.models.fee.fee_plan import FeePlan
    from app.models.fee.fee_assignment import FeeAssignment

    plan = FeePlan(name="Seed Plan", academic_year="2025-26", frequency="monthly")
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    # Create an assignment linking the student to the plan
    assignment = FeeAssignment(
        student_id=seed_student.id,
        fee_plan_id=plan.id,
        concession=0,
        note="seed assignment",
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    return plan
