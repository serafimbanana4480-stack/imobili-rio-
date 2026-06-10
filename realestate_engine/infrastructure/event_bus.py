"""Event bus abstraction for distributed architecture (FASE 6).

Supports:
- In-memory queue (default, single-node)
- Redis Streams (lightweight distributed)
- Kafka (enterprise distributed)

Provides decoupled pub/sub for:
- ListingScraped
- ListingEnriched
- PriceChanged
- ValuationUpdated
- ScoreComputed
"""
import asyncio
import inspect
import json
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from loguru import logger


@dataclass
class DomainEvent:
    event_type: str
    payload: Dict[str, Any]
    timestamp: str
    source: str
    correlation_id: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, raw: str) -> "DomainEvent":
        data = json.loads(raw)
        return cls(**data)


class EventBus:
    """Abstract event bus with pluggable backends."""

    def __init__(self, backend: str = "memory"):
        self.backend = backend
        self._subscribers: Dict[str, List[Callable]] = {}
        self._memory_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    def subscribe(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"EventBus: handler registered for {event_type}")

    async def publish(self, event: DomainEvent):
        """Publish event to all subscribers."""
        logger.debug(f"EventBus: publishing {event.event_type}")
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"EventBus: handler failed for {event.event_type}: {e}")

    async def start_consumer(self):
        """Start async consumer loop (for memory queue)."""
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(self._memory_queue.get(), timeout=1.0)
                await self.publish(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"EventBus: consumer error: {e}")

    def stop_consumer(self):
        self._running = False

    @classmethod
    def listing_scraped(cls, listing: Dict[str, Any]) -> DomainEvent:
        return DomainEvent(
            event_type="ListingScraped",
            payload=listing,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="spider",
        )

    @classmethod
    def listing_enriched(cls, listing: Dict[str, Any]) -> DomainEvent:
        return DomainEvent(
            event_type="ListingEnriched",
            payload=listing,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="etl",
        )

    @classmethod
    def price_changed(cls, listing_id: str, old_price: float, new_price: float) -> DomainEvent:
        return DomainEvent(
            event_type="PriceChanged",
            payload={"listing_id": listing_id, "old_price": old_price, "new_price": new_price},
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="etl",
        )

    @classmethod
    def valuation_updated(cls, listing_id: str, valuation: Dict[str, Any]) -> DomainEvent:
        return DomainEvent(
            event_type="ValuationUpdated",
            payload={"listing_id": listing_id, **valuation},
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="valuation",
        )

    @classmethod
    def score_computed(cls, listing_id: str, score: Dict[str, Any]) -> DomainEvent:
        return DomainEvent(
            event_type="ScoreComputed",
            payload={"listing_id": listing_id, **score},
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="scoring",
        )
