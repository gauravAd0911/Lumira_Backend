"""Outbox relay infrastructure for background event dispatch."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.constants import (
    OUTBOX_BATCH_SIZE,
    OUTBOX_POLL_INTERVAL_SECONDS,
    OUTBOX_STATUS_DISPATCHED,
    OUTBOX_STATUS_FAILED,
    OUTBOX_STATUS_PENDING,
)
from app.db.session import get_session_factory
from app.models.models import OutboxEvent

logger = logging.getLogger(__name__)


class BrokerClient:
    """Development broker stub that logs dispatched events."""

    async def publish(self, *, event_type: str, aggregate_id: str, payload: dict) -> None:
        logger.info(
            "Dispatched outbox event type=%s aggregate_id=%s payload=%s",
            event_type,
            aggregate_id,
            payload,
        )


class OutboxRelayWorker:
    """Poll pending outbox rows and relay them through the broker."""

    def __init__(
        self,
        broker: BrokerClient,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        poll_interval_seconds: int = OUTBOX_POLL_INTERVAL_SECONDS,
        batch_size: int = OUTBOX_BATCH_SIZE,
    ) -> None:
        self._broker = broker
        self._session_factory = session_factory
        self._poll_interval_seconds = max(1, poll_interval_seconds)
        self._batch_size = max(1, batch_size)
        self._stop_event = asyncio.Event()
        self._disabled_reason: str | None = None

    async def start(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._run_once()
            except ModuleNotFoundError as exc:
                self._disabled_reason = (
                    "Outbox relay disabled because the current Python interpreter "
                    f"is missing required dependency '{exc.name}'. "
                    "Run the API with the project virtual environment."
                )
                logger.warning(self._disabled_reason)
                self._stop_event.set()
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Outbox relay cycle failed.")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_interval_seconds)
            except asyncio.TimeoutError:
                continue

    async def stop(self) -> None:
        self._stop_event.set()

    async def _run_once(self) -> None:
        session_factory = self._session_factory or get_session_factory()
        async with session_factory() as session:
            pending_events = await self._get_pending_events(session)
            if not pending_events:
                return

            for event in pending_events:
                try:
                    await self._broker.publish(
                        event_type=event.event_type,
                        aggregate_id=event.aggregate_id,
                        payload=event.payload,
                    )
                    event.status = OUTBOX_STATUS_DISPATCHED
                    event.dispatched_at = datetime.utcnow()
                except Exception as exc:
                    logger.exception("Failed to dispatch outbox event %s.", event.event_id)
                    event.status = OUTBOX_STATUS_FAILED
                    event.payload = {**event.payload, "dispatch_error": str(exc)}

            await session.commit()

    async def _get_pending_events(self, session: AsyncSession) -> list[OutboxEvent]:
        query = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OUTBOX_STATUS_PENDING)
            .order_by(OutboxEvent.created_at.asc())
            .limit(self._batch_size)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
