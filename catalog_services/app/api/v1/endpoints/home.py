"""GET /api/v1/home — home page content endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.catalog import HomeResponse
from app.services.catalog_service import CatalogService
from app.utils.dependencies import get_catalog_service

router = APIRouter()


@router.get(
    "/home",
    summary="Home page content",
    description=(
        "Returns active banners, featured products, and top-level categories "
        "for rendering the home page."
    ),
)
async def get_home(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> HomeResponse:
    """Return composite home page data."""
    return await service.get_home()