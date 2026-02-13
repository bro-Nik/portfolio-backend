from fastapi import APIRouter

from .internal import internal_router
from .user import user_router

api_router = APIRouter()

api_router.include_router(internal_router)
api_router.include_router(user_router)
