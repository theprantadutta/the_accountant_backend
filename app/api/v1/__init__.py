"""API v1 routes"""
from fastapi import APIRouter
from app.api.v1 import auth, auth_firebase

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(auth_firebase.router, prefix="/auth", tags=["authentication"])
