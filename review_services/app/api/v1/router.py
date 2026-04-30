"""API v1 router."""
from fastapi import APIRouter
from app.api.v1.endpoints.reviews import router as reviews_router
 
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(reviews_router)