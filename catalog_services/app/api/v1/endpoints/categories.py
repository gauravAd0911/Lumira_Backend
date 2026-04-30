"""GET /api/v1/categories — categories listing endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.catalog import CategoryListResponse
from app.services.catalog_service import CatalogService
from app.utils.dependencies import get_catalog_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    summary="List categories",
    description="Returns all active categories ordered by sort_order.",
)
async def list_categories(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> CategoryListResponse:
    """Return all active product categories."""
    return await service.list_categories()