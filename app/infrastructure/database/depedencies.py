# database/dependencies.py
from typing import AsyncIterator, Iterator, Optional
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.manager import db_manager


# ==================== SYNC DEPENDENCIES ====================

def get_db(db_name: Optional[str] = None) -> Iterator[Session]:
    """
    FastAPI dependency for sync database session
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    with db_manager.session(db_name) as session:
        yield session


def get_primary_db() -> Iterator[Session]:
    """Get primary database session (sync)"""
    yield from get_db(None)  # ✅ FIX: yield from


def get_replica_db() -> Iterator[Session]:
    """Get replica database session (sync)"""
    yield from get_db("replica")  # ✅ FIX: yield from


def get_analytics_db() -> Iterator[Session]:
    """Get analytics database session (sync)"""
    yield from get_db("analytics")  # ✅ FIX: yield from


# ==================== ASYNC DEPENDENCIES ====================

async def get_async_db(db_name: Optional[str] = None) -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency for async database session
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    async with db_manager.async_session(db_name) as session:
        yield session


async def get_async_primary_db() -> AsyncIterator[AsyncSession]:
    """Get primary database session (async)"""
    async for session in get_async_db(None):  # ✅ FIX: async for
        yield session


async def get_async_replica_db() -> AsyncIterator[AsyncSession]:
    """Get replica database session (async)"""
    async for session in get_async_db("replica"):  # ✅ FIX: async for
        yield session


async def get_async_analytics_db() -> AsyncIterator[AsyncSession]:
    """Get analytics database session (async)"""
    async for session in get_async_db("analytics"):  # ✅ FIX: async for
        yield session


# ==================== FACTORY FUNCTIONS ====================

def create_db_dependency(db_name: str):
    """
    Factory to create custom sync database dependency
    
    Usage:
        get_cache_db = create_db_dependency("cache")
        
        @app.get("/cached")
        def get_cached(db: Session = Depends(get_cache_db)):
            ...
    """
    def dependency() -> Iterator[Session]:
        yield from get_db(db_name)  # ✅ FIX: yield from
    return dependency


def create_async_db_dependency(db_name: str):
    """
    Factory to create custom async database dependency
    
    Usage:
        get_async_cache_db = create_async_db_dependency("cache")
        
        @app.get("/cached")
        async def get_cached(db: AsyncSession = Depends(get_async_cache_db)):
            ...
    """
    async def dependency() -> AsyncIterator[AsyncSession]:
        async for session in get_async_db(db_name):  # ✅ FIX: async for
            yield session
    return dependency