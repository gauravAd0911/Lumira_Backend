"""FastAPI dependency providers for service-layer objects."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.catalog_service import CatalogService


def get_catalog_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CatalogService:
    """Inject a CatalogService with a scoped database session."""
    return CatalogService(session)