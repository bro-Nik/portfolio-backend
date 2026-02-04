from fastapi import APIRouter

from .admin import admin_router
from .user import user_router

api_router = APIRouter(prefix='/api')

api_router.include_router(admin_router)
api_router.include_router(user_router)
