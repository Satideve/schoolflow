# backend/app/models/__init__.py

from .class_section import ClassSection
from .student import Student
from .user import User

# Import fee-related models so they are registered in the ORM
from .fee import (
    FeePlan,
    FeeComponent,
    FeePlanComponent,
    FeeAssignment,
    FeeInvoice,
    Payment,
    Receipt,
)
