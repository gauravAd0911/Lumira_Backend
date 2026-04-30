"""Authentication utilities and FastAPI dependency for current user."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

_bearer_scheme = HTTPBearer()


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT, returning its payload.

    Args:
        token: Raw JWT string.

    Returns:
        Decoded claims dictionary.

    Raises:
        HTTPException: 401 when the token is invalid or expired.
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> str:
    """FastAPI dependency that extracts the authenticated user ID from the JWT.

    Args:
        credentials: Bearer token extracted by the HTTPBearer scheme.

    Returns:
        The ``sub`` claim (user UUID) from the token.

    Raises:
        HTTPException: 401 when ``sub`` is absent from the token payload.
    """
    payload = _decode_token(credentials.credentials)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


CurrentUserId = Annotated[str, Depends(get_current_user_id)]