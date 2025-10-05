from typing import AsyncIterator, Generator, Optional
from .manager import database_manager
from sqlmodel import Session

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)


def get_db(db_name: Optional[str] = None) -> Generator[Session, None, None]:
    """FastAPI dependency for getting database session (sync)"""
    with database_manager.session_scope(db_name) as session:
        yield session


async def get_async_db(db_name: Optional[str] = None) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for getting database session (async)"""
    db = database_manager.get_database(db_name)
    async with db.get_async_session() as session:
        yield session


def get_primary_db() -> Generator[Session, None, None]:
    """Get primary database session"""
    return get_db(None)


def get_replica_db() -> Generator[Session, None, None]:
    """Get replica database session"""
    return get_db("replica")


def get_analytics_db() -> Generator[Session, None, None]:
    """Get analytics database session"""
    return get_db("analytics")


async def get_async_primary_db() -> AsyncIterator[AsyncSession]:
    """Get async primary database session"""
    return get_async_db(None)


async def get_async_replica_db() -> AsyncIterator[AsyncSession]:
    """Get async replica database session"""
    return get_async_db("replica")


async def get_async_analytics_db() -> AsyncIterator[AsyncSession]:
    """Get async analytics database session"""
    return get_async_db("analytics")


def create_db_dependency(db_name: str):
    """Factory function to create custom database dependency"""
    def dependency() -> Generator[Session, None, None]:
        return get_db(db_name)
    return dependency


def create_async_db_dependency(db_name: str):
    """Factory function to create custom async database dependency"""
    async def dependency() -> AsyncIterator[AsyncSession]:
        return get_async_db(db_name)
    return dependency