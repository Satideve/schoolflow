# backend/app/api/v1/routers/class_sections.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.schemas.class_section import ClassSectionCreate, ClassSectionOut
from app.repositories.class_section_repo import (
    create_class_section,
    get_class_section,
    list_class_sections,
)
from app.db.session import get_db

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
