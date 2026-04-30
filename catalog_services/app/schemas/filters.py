"""Validated query parameter models for catalog endpoints."""

from typing import Any, Optional

from fastapi import HTTPException, Query, status
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.config import settings
from app.core.constants import ALLOWED_SORT_VALUES, MIN_LIMIT, MIN_PAGE

_ALLOWED_SORT_DISPLAY: str = ", ".join(sorted(ALLOWED_SORT_VALUES))


def _safe_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Strip non-JSON-serialisable objects from Pydantic v2 error ctx.

    Pydantic v2 puts the raw Exception instance inside ctx['error'].
    Python's json.dumps cannot serialise Exception objects, causing Starlette
    to crash with TypeError when building the JSONResponse.
    This helper converts every ctx value to str so the payload is always safe.
    """
    clean: list[dict[str, Any]] = []
    for err in exc.errors(include_url=False):
        entry: dict[str, Any] = {
            "type":  err.get("type"),
            "loc":   list(err.get("loc", [])),
            "msg":   err.get("msg"),
            "input": err.get("input"),
        }
        if ctx := err.get("ctx"):
            entry["ctx"] = {k: str(v) for k, v in ctx.items()}
        clean.append(entry)
    return clean


class ProductFilterParams(BaseModel):
    """Server-side filter and pagination parameters for GET /products."""

    q:         Optional[str]   = Field(None, description="Full-text search query")
    category:  Optional[str]   = Field(None, description="Category slug")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price (inclusive)")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price (inclusive)")
    skin_type: Optional[str]   = Field(None, description="Target skin type")
    sort:      Optional[str]   = Field(
        None,
        description=f"Sort order. Allowed: {_ALLOWED_SORT_DISPLAY}",
    )
    page:  int = Field(settings.DEFAULT_PAGE,  ge=MIN_PAGE)
    limit: int = Field(settings.DEFAULT_LIMIT, ge=MIN_LIMIT, le=settings.MAX_LIMIT)

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, value: Optional[str]) -> Optional[str]:
        """Reject unknown sort keys early to prevent SQL injection risk."""
        if value is not None and value not in ALLOWED_SORT_VALUES:
            raise ValueError(
                f"Invalid sort '{value}'. Allowed: {_ALLOWED_SORT_DISPLAY}"
            )
        return value

    @field_validator("price_max")
    @classmethod
    def validate_price_range(cls, price_max: Optional[float], info) -> Optional[float]:
        """Ensure price_max is not below price_min when both are provided."""
        price_min = info.data.get("price_min")
        if price_min is not None and price_max is not None and price_max < price_min:
            raise ValueError(
                f"price_max ({price_max}) must be >= price_min ({price_min})"
            )
        return price_max


def product_filter_params(
    q:         Optional[str]   = Query(None,                   description="Search query"),
    category:  Optional[str]   = Query(None,                   description="Category slug"),
    price_min: Optional[float] = Query(None, ge=0,             description="Min price"),
    price_max: Optional[float] = Query(None, ge=0,             description="Max price"),
    skin_type: Optional[str]   = Query(None,                   description="Skin type"),
    sort:      Optional[str]   = Query(None,                   description=f"Sort. Allowed: {_ALLOWED_SORT_DISPLAY}"),
    page:      int             = Query(settings.DEFAULT_PAGE,  ge=MIN_PAGE),
    limit:     int             = Query(settings.DEFAULT_LIMIT, ge=MIN_LIMIT, le=settings.MAX_LIMIT),
) -> ProductFilterParams:
    """Parse and validate product filter query params.

    Always returns HTTP 422 with a fully JSON-serialisable body on error —
    never lets a raw ValidationError or TypeError bubble up to a 500.
    """
    try:
        return ProductFilterParams(
            q=q, category=category,
            price_min=price_min, price_max=price_max,
            skin_type=skin_type, sort=sort,
            page=page, limit=limit,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_safe_errors(exc),
        ) from exc