# backend/app/db/base.py

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Dynamically import models to avoid circular imports and ensure Alembic sees them
def load_all_models():
    import importlib

    # Core/domain models
    importlib.import_module("app.models.user")
    importlib.import_module("app.models.student")
    importlib.import_module("app.models.class_section")
    importlib.import_module("app.models.parent")
    importlib.import_module("app.models.staff")
    importlib.import_module("app.models.setting")
    importlib.import_module("app.models.audit_log")

    # Fee-related models
    importlib.import_module("app.models.fee.fee_plan")
    importlib.import_module("app.models.fee.fee_component")
    importlib.import_module("app.models.fee.fee_plan_component")
    importlib.import_module("app.models.fee.fee_assignment")
    importlib.import_module("app.models.fee.fee_invoice")
    importlib.import_module("app.models.fee.payment")
    importlib.import_module("app.models.fee.receipt")

load_all_models()
