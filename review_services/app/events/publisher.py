"""Transactional outbox publisher for review domain events."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    EVENT_REVIEW_CREATED,
    EVENT_REVIEW_UPDATED,
    OUTBOX_STATUS_PENDING,
)
from app.models.models import OutboxEvent, Review


class EventPublisher:
    """Persist domain events to the outbox in the current transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def publish_review_created(self, review: Review) -> None:
        await self._enqueue(EVENT_REVIEW_CREATED, review)

    async def publish_review_updated(self, review: Review) -> None:
        await self._enqueue(EVENT_REVIEW_UPDATED, review)

    async def _enqueue(self, event_type: str, review: Review) -> None:
        event = OutboxEvent(
            event_type=event_type,
            aggregate_id=review.review_id,
            payload={
                "review_id": review.review_id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "rating": review.rating,
                "title": review.title,
                "body": review.body,
                "is_verified": review.is_verified,
                "status": review.status,
                "created_at": review.created_at.isoformat(),
                "updated_at": review.updated_at.isoformat(),
            },
            status=OUTBOX_STATUS_PENDING,
        )
        self._session.add(event)
        await self._session.flush()
