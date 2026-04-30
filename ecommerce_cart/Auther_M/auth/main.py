from __future__ import annotations

import os
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import Base, engine
from auth.routes.auth import router as auth_router
from auth.routes.protected import router as protected_router

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=str(ROOT_DIR / ".env"), override=True)

SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-prod")
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FAST MySQL Auth")
security = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def verify_token(token: str) -> dict | None:
    """Decode JWT token."""

    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_current_user(token=Depends(security)) -> dict:
    """Resolve the JWT payload from the Authorization header."""

    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


def require_role(required_role: str):
    """Dependency factory for role-based access checks."""

    def decorator(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Access denied")
        return current_user

    return decorator


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(protected_router, prefix="/protected", tags=["Protected"])


@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/welcome")
def welcome_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/protected/user")
async def protected_user(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "message": "User access granted",
        "data": {
            "user_id": current_user.get("user_id"),
            "role": current_user.get("role"),
        },
    }


@app.get("/protected/admin")
async def protected_admin(current_user: dict = Depends(require_role("admin"))):
    return {
        "success": True,
        "message": "Admin access granted",
        "data": {
            "user_id": current_user.get("user_id"),
            "role": current_user.get("role"),
        },
    }
