"""Product endpoints: list, detail, related, and filter options."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.catalog import (
    FilterOptionsResponse,
    ProductDetailSchema,
    ProductListResponse,
)
from app.schemas.filters import ProductFilterParams, product_filter_params
from app.services.catalog_service import CatalogService
from app.utils.dependencies import get_catalog_service

router = APIRouter(prefix="/products", tags=["Products"])

_PRODUCT_NOT_FOUND = "Product not found."


@router.get(
    "",
    summary="List products",
    description=(
        "Returns a filtered, sorted, paginated list of active products. "
        "Supports q, category, price_min, price_max, skin_type, sort, page, limit."
    ),
)
async def list_products(
    params: Annotated[ProductFilterParams, Depends(product_filter_params)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductListResponse:
    """Return products matching the supplied filter parameters."""
    return await service.list_products(params)


@router.get(
    "/filters",
    summary="Available filter options",
    description="Returns all filter facets (categories, skin types, price range, sort options) "
    "derived from live product data.",
)
async def get_filter_options(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> FilterOptionsResponse:
    """Return aggregated filter facet data for the product listing UI."""
    return await service.get_filter_options()


@router.get(
    "/{product_id}",
    summary="Product detail",
    description="Returns full product data including images, ingredients, benefits, and stock.",
)
async def get_product(
    product_id: int,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailSchema:
    """Return detail for a single active product."""
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PRODUCT_NOT_FOUND)
    return product


@router.get(
    "/{product_id}/related",
    summary="Related products (optional)",
    description="Returns products from the same category, ordered by rating.",
)
async def get_related_products(
    product_id: int,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    limit: Annotated[int, Query(ge=1, le=20)] = 6,
) -> ProductListResponse:
    """Return products related to the given product by category."""
    result = await service.get_related_products(product_id, limit=limit)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PRODUCT_NOT_FOUND)
    return result