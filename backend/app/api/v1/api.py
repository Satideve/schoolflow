# C:\coding_projects\dev\schoolflow\backend\app\api\v1\api.py

from fastapi import APIRouter

from app.api.v1.routers import auth, health, class_sections, students, pdf
from app.api.v1.routers.fees import plans, invoices, payments
from app.api.v1.routers.fees.receipts import router as receipts_router
from app.api.v1.routers.users import router as users_router
from app.api.v1.routers.fees.fee_components import router as fee_components_router
from app.api.v1.routers.auth_me import router as auth_me_router
from app.api.v1.routers.fees.assignments import router as fee_assignments_router
from app.api.v1.routers.fees.plan_components import router as fee_plan_components_router
from app.api.v1.routers.admin.csv_import import router as admin_csv_router

api_router = APIRouter()

# Core routers
api_router.include_router(auth.router)
api_router.include_router(auth_me_router)
api_router.include_router(health.router)
api_router.include_router(class_sections.router)
api_router.include_router(students.router)
api_router.include_router(pdf.router)

# Fee-related routers
api_router.include_router(plans.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(receipts_router)
api_router.include_router(fee_components_router)
api_router.include_router(fee_assignments_router)
api_router.include_router(fee_plan_components_router)

# Admin CSV import
api_router.include_router(admin_csv_router)

# User management
api_router.include_router(users_router)
