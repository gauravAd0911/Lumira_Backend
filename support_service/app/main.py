# main.py

from fastapi import FastAPI
from app.api.support_routes import router as support_router
from app.models.user_model import User

app = FastAPI(title="Support Service")

app.include_router(support_router)