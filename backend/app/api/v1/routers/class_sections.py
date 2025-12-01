# backend/app/api/v1/routers/class_sections.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.class_section import ClassSection
from app.repositories.class_section_repo import (
    create_class_section,
    get_class_section,
    list_class_sections,
)
from app.schemas.class_section import (
    ClassSectionCreate,
    ClassSectionOut,
    ClassSectionUpdate,
)

router = APIRouter(
    prefix="/api/v1/class-sections",
    tags=["class_sections"],
)


@router.post("/", response_model=ClassSectionOut, status_code=status.HTTP_201_CREATED)
def create_section(
    section_in: ClassSectionCreate,
    db: Session = Depends(get_db),
):
    return create_class_section(db, section_in)


@router.get("/", response_model=List[ClassSectionOut])
def read_sections(db: Session = Depends(get_db)):
    return list_class_sections(db)


@router.get("/{section_id}", response_model=ClassSectionOut)
def read_section(
    section_id: int,
    db: Session = Depends(get_db),
):
    section = get_class_section(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


@router.patch("/{section_id}", response_model=ClassSectionOut)
def update_section(
    section_id: int,
    section_in: ClassSectionUpdate,
    db: Session = Depends(get_db),
):
    section = db.get(ClassSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section_in.name is not None:
        section.name = section_in.name
    if section_in.academic_year is not None:
        section.academic_year = section_in.academic_year

    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
):
    section = db.get(ClassSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        db.delete(section)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Likely there are students referencing this section
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete section because it is referenced by other records.",
        )
    return None
