# backend/app/api/v1/api.py

from fastapi import APIRouter

from app.api.v1.routers import auth, health, class_sections, students, pdf
from app.api.v1.routers.fees import plans, invoices, payments
from app.api.v1.routers.fees.receipts import router as receipts_router

api_router = APIRouter()

# Core routers
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(class_sections.router)
api_router.include_router(students.router)
api_router.include_router(pdf.router)

# Fee-related routers
api_router.include_router(plans.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(receipts_router)
