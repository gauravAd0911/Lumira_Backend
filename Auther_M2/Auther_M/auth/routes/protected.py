from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from auth.middleware.auth_guard import get_current_user
from auth.models.user import User

router = APIRouter()


@router.get("/user")
async def protected_user(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "success": True,
        "message": "User access granted",
        "data": {
            "user_id": str(current_user.id),
            "role": current_user.role.value,
        },
    }


@router.get(
    "/admin",
    responses={
        403: {"description": "Admin access required"},
    },
)
async def protected_admin(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "success": True,
        "message": "Admin access granted",
        "data": {"message": "Admin only content"},
    }
