from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import get_user_from_token

_bearer_scheme = HTTPBearer(auto_error=False)


# =========================
# DATABASE DEPENDENCY
# =========================
def get_db():
    """
    Provides DB session for each request.
    Automatically closes after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
):
    """
    Resolve the current user from JWT first, then a development X-User-Id
    header for local service testing.
    """
    if credentials:
        user_id = get_user_from_token(credentials.credentials)
        if user_id:
            return user_id

    if x_user_id:
        return x_user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
    )


# =========================
# FUTURE: JWT AUTH (READY STRUCTURE)
# =========================
def get_current_user(
    user_id: str = Depends(get_current_user_id),
):
    """
    Placeholder for real authentication.
    Later:
    - decode JWT
    - validate token
    - fetch user
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    return user_id
