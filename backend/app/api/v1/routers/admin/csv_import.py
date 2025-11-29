# backend/app/api/v1/routers/admin/csv_import.py
import csv
import io
from typing import List, Tuple, Dict

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Security, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.api.v1.routers.auth import get_current_user

from app.schemas.class_section import ClassSectionCreate, ClassSectionOut
from app.models.class_section import ClassSection

from app.schemas.student import StudentCreate, StudentOut
from app.models.student import Student

from app.schemas.fee.plan import FeePlanOut
from app.models.fee.fee_plan import FeePlan
from app.models.fee.fee_component import FeeComponent
from app.models.fee.fee_plan_component import FeePlanComponent

router = APIRouter(
    prefix="/api/v1/admin/csv",
    tags=["admin", "csv-import"],
)


def _require_admin_like(current_user) -> None:
    role = getattr(current_user, "role", None)
    if role not in {"admin", "clerk", "accountant"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Admin role required for CSV import"},
        )


def _read_csv(file: UploadFile) -> csv.DictReader:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_file", "message": "Only .csv files are supported"},
        )

    try:
        raw = file.file.read()
        text = raw.decode("utf-8-sig")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "read_error", "message": "Failed to read uploaded file"},
        )

    return csv.DictReader(io.StringIO(text))


# ---------------------------------------------------------------------------
# CLASS SECTIONS (idempotent by name + academic_year)
# ---------------------------------------------------------------------------
@router.post(
    "/class-sections",
    response_model=List[ClassSectionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk import class sections from CSV",
)
async def import_class_sections_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    CSV columns expected (minimum):
    - name
    - academic_year

    Extra columns like id, standard, section, capacity are ignored.

    Compatible with ops/seeds/class_sections.csv when headers include:
    id,name,standard,section,capacity,academic_year

    Idempotent behavior:
    - If a class section with the same (name, academic_year) already exists, that row is skipped.
    """
    _require_admin_like(current_user)

    reader = _read_csv(file)
    required_columns = {"name", "academic_year"}
    missing = required_columns - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_header",
                "message": f"Missing required columns: {', '.join(sorted(missing))}",
            },
        )

    created: List[ClassSection] = []

    try:
        for row in reader:
            name = (row.get("name") or "").strip()
            year = (row.get("academic_year") or "").strip()
            if not name or not year:
                continue

            # Idempotent check: skip if (name, academic_year) already exists
            existing = (
                db.query(ClassSection)
                .filter(
                    ClassSection.name == name,
                    ClassSection.academic_year == year,
                )
                .first()
            )
            if existing:
                continue

            payload = ClassSectionCreate(name=name, academic_year=year)
            obj = ClassSection(name=payload.name, academic_year=payload.academic_year)
            db.add(obj)
            created.append(obj)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "import_failed", "message": str(exc)},
        )

    for obj in created:
        db.refresh(obj)

    return [ClassSectionOut.model_validate(obj) for obj in created]


# ---------------------------------------------------------------------------
# STUDENTS (idempotent by roll_number)
# ---------------------------------------------------------------------------
@router.post(
    "/students",
    response_model=List[StudentOut],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk import students from CSV",
)
async def import_students_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    CSV columns expected (minimum):
    - name
    - roll_number
    - class_section_id

    Extra columns (like id, parent_email) are ignored.

    Compatible with ops/seeds/students.csv:
    id,name,roll_number,class_section_id,parent_email

    Idempotent behavior:
    - If a student with the same roll_number already exists, that row is skipped.
    """
    _require_admin_like(current_user)

    reader = _read_csv(file)
    required_columns = {"name", "roll_number", "class_section_id"}
    missing = required_columns - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_header",
                "message": f"Missing required columns: {', '.join(sorted(missing))}",
            },
        )

    created: List[Student] = []

    try:
        for row in reader:
            name = (row.get("name") or "").strip()
            roll_number = (row.get("roll_number") or "").strip()
            class_section_raw = (row.get("class_section_id") or "").strip()

            if not name or not roll_number or not class_section_raw:
                continue

            try:
                class_section_id = int(class_section_raw)
            except ValueError:
                continue

            # Idempotent check: skip if this roll_number already exists
            existing = (
                db.query(Student)
                .filter(Student.roll_number == roll_number)
                .first()
            )
            if existing:
                continue

            payload = StudentCreate(
                name=name,
                roll_number=roll_number,
                class_section_id=class_section_id,
            )
            obj = Student(
                name=payload.name,
                roll_number=payload.roll_number,
                class_section_id=payload.class_section_id,
            )
            db.add(obj)
            created.append(obj)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "import_failed", "message": str(exc)},
        )

    for obj in created:
        db.refresh(obj)

    return [StudentOut.model_validate(obj) for obj in created]


# ---------------------------------------------------------------------------
# FEE PLANS + COMPONENTS (from seed_fees.csv)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-plans",
    response_model=List[FeePlanOut],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk import fee plans + components from CSV",
)
async def import_fee_plans_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),
):
    """
    CSV columns expected (compatible with ops/seeds/seed_fees.csv):

    - fee_plan_name
    - academic_year
    - frequency
    - component_name
    - amount
    - is_mandatory   (currently ignored by the DB model; kept for future use)
    """
    _require_admin_like(current_user)

    reader = _read_csv(file)
    required_columns = {
        "fee_plan_name",
        "academic_year",
        "frequency",
        "component_name",
        "amount",
    }
    missing = required_columns - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_header",
                "message": f"Missing required columns: {', '.join(sorted(missing))}",
            },
        )

    plan_cache: Dict[Tuple[str, str, str], FeePlan] = {}
    component_cache: Dict[str, FeeComponent] = {}
    touched_plans: Dict[int, FeePlan] = {}

    try:
        for row in reader:
            plan_name = (row.get("fee_plan_name") or "").strip()
            academic_year = (row.get("academic_year") or "").strip()
            frequency = (row.get("frequency") or "").strip()
            component_name = (row.get("component_name") or "").strip()
            amount_raw = (row.get("amount") or "").strip()

            if not plan_name or not academic_year or not frequency or not component_name or not amount_raw:
                continue

            try:
                amount_value = float(amount_raw)
            except ValueError:
                continue

            plan_key = (plan_name, academic_year, frequency)
            plan = plan_cache.get(plan_key)
            if plan is None:
                plan = (
                    db.query(FeePlan)
                    .filter(
                        FeePlan.name == plan_name,
                        FeePlan.academic_year == academic_year,
                        FeePlan.frequency == frequency,
                    )
                    .first()
                )
                if plan is None:
                    plan = FeePlan(
                        name=plan_name,
                        academic_year=academic_year,
                        frequency=frequency,
                    )
                    db.add(plan)
                    db.flush()
                plan_cache[plan_key] = plan

            touched_plans[plan.id] = plan

            component = component_cache.get(component_name)
            if component is None:
                component = (
                    db.query(FeeComponent)
                    .filter(FeeComponent.name == component_name)
                    .first()
                )
                if component is None:
                    component = FeeComponent(
                        name=component_name,
                        description=component_name,
                    )
                    db.add(component)
                    db.flush()
                component_cache[component_name] = component

            existing_fpc = (
                db.query(FeePlanComponent)
                .filter(
                    FeePlanComponent.fee_plan_id == plan.id,
                    FeePlanComponent.fee_component_id == component.id,
                )
                .first()
            )
            if existing_fpc:
                existing_fpc.amount = amount_value
            else:
                fpc = FeePlanComponent(
                    fee_plan_id=plan.id,
                    fee_component_id=component.id,
                    amount=amount_value,
                )
                db.add(fpc)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "import_failed", "message": str(exc)},
        )

    result_plans: List[FeePlan] = []
    for plan in touched_plans.values():
        db.refresh(plan)
        result_plans.append(plan)

    return [FeePlanOut.model_validate(p) for p in result_plans]
