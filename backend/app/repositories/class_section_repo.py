# backend/app/repositories/class_section_repo.py

from sqlalchemy.orm import Session
from app.models.class_section import ClassSection
from app.schemas.class_section import ClassSectionCreate

def create_class_section(
    db: Session, section_in: ClassSectionCreate
) -> ClassSection:
    db_obj = ClassSection(**section_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_class_section(
    db: Session, section_id: int
) -> ClassSection | None:
    return db.query(ClassSection).filter(ClassSection.id == section_id).first()

def list_class_sections(db: Session) -> list[ClassSection]:
    return db.query(ClassSection).all()
