"""Banner repository: fetches home page promotional banners."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import HomeBanner


class BannerRepository:
    """Data-access layer for HomeBanner entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self, limit: int) -> list[HomeBanner]:
        """Return active banners ordered by sort_order."""
        query = (
            select(HomeBanner)
            .where(HomeBanner.is_active.is_(True))
            .order_by(HomeBanner.sort_order)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())