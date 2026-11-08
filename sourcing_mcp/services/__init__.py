"""Service layer base classes and utilities."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from ..database import db


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self):
        self.db = db

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service dependencies."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check service health."""
        pass


class EventPublisher:
    """Publish domain events."""

    async def publish(
        self,
        stream_type: str,
        stream_id: UUID,
        event_type: str,
        actor_type: str,
        actor_id: Optional[str],
        payload: dict[str, Any],
        project_id: Optional[UUID] = None,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
    ) -> int:
        """Publish an event to the event store."""
        async with db.transaction() as conn:
            result = await conn.execute(
                """
                INSERT INTO event (
                    stream_type, stream_id, project_id, type,
                    actor_type, actor_id, payload,
                    correlation_id, causation_id, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING seq
                """,
                [
                    stream_type,
                    stream_id,
                    project_id,
                    event_type,
                    actor_type,
                    actor_id,
                    payload,
                    correlation_id,
                    causation_id,
                    {},  # metadata
                ],
            )
            row = await result.fetchone()
            return row["seq"]


class ServiceRegistry:
    """Central registry for all services."""

    def __init__(self):
        self._services: dict[str, BaseService] = {}

    def register(self, name: str, service: BaseService) -> None:
        """Register a service."""
        self._services[name] = service

    def get(self, name: str) -> BaseService:
        """Get a registered service."""
        if name not in self._services:
            raise ValueError(f"Service not registered: {name}")
        return self._services[name]

    async def initialize_all(self) -> None:
        """Initialize all registered services."""
        for service in self._services.values():
            await service.initialize()

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """Run health checks on all services."""
        results = {}
        for name, service in self._services.items():
            try:
                results[name] = await service.health_check()
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
        return results


# Global service registry
registry = ServiceRegistry()
