from fastapi import APIRouter

from app.api.admin.endpoints import admin

admin_router = APIRouter(prefix='/admin')

admin_router.include_router(admin.router)
