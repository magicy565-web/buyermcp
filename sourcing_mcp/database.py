"""Database connection and session management."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .config import config

logger = logging.getLogger(__name__)


class Database:
    """Database connection pool manager."""

    def __init__(self) -> None:
        self.pool: AsyncConnectionPool | None = None

    async def connect(self) -> None:
        """Initialize connection pool."""
        if self.pool is not None:
            return

        logger.info(f"Connecting to database: {config.DATABASE_URL.split('@')[-1]}")
        self.pool = AsyncConnectionPool(
            conninfo=config.DATABASE_URL,
            min_size=2,
            max_size=10,
            timeout=30.0,
            kwargs={"row_factory": dict_row},
        )
        await self.pool.open()
        logger.info("Database connection pool initialized")

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        """Get a connection from the pool."""
        if self.pool is None:
            raise RuntimeError("Database not connected")
        async with self.pool.connection() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        """Get a connection with automatic transaction management."""
        async with self.connection() as conn:
            async with conn.transaction():
                yield conn


# Global database instance
db = Database()
