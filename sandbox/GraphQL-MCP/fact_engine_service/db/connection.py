"""Database connection management"""
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

try:
    import psycopg2
    from psycopg2.pool import ThreadedConnectionPool
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    ThreadedConnectionPool = None

from typing import Optional, Any
import logging
from contextlib import contextmanager

from config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections (sync and async)"""
    
    def __init__(self):
        self._sync_pool: Optional[Any] = None
        self._async_pool: Optional[Any] = None
    
    def get_sync_connection(self):
        """Get a synchronous database connection"""
        if not HAS_PSYCOPG2:
            raise ImportError("psycopg2 is not installed. Install with: pip install psycopg2-binary")
        if not self._sync_pool:
            self._sync_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )
        return self._sync_pool.getconn()
    
    def return_sync_connection(self, conn):
        """Return a connection to the pool"""
        if self._sync_pool:
            self._sync_pool.putconn(conn)
    
    @contextmanager
    def sync_connection(self):
        """Context manager for sync connections"""
        if not HAS_PSYCOPG2:
            raise ImportError("psycopg2 is not installed. Install with: pip install psycopg2-binary")
        conn = self.get_sync_connection()
        try:
            yield conn
        finally:
            self.return_sync_connection(conn)
    
    async def get_async_pool(self):
        """Get async connection pool"""
        if not HAS_ASYNCPG:
            raise ImportError("asyncpg is not installed. Install with: pip install asyncpg")
        if not self._async_pool:
            self._async_pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=1,
                max_size=10
            )
        return self._async_pool
    
    async def close(self):
        """Close all connections"""
        if self._async_pool:
            await self._async_pool.close()
        if self._sync_pool:
            self._sync_pool.closeall()


# Global database connection instance
db = DatabaseConnection()

