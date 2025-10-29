# database/connection.py
from typing import Optional, Iterator, AsyncIterator
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import Engine, create_engine, StaticPool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import QueuePool, NullPool
from sqlmodel import SQLModel, Session
import logging

from app.config.database import DatabaseSettings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Single database connection handler
    Manages both sync and async connections for one database
    """
    
    def __init__(self, name: str, settings: DatabaseSettings):
        self.name = name
        self.settings = settings
        
        # Engines
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._async_session_maker: Optional[async_sessionmaker] = None
        
        # State
        self._is_connected = False
    
    def _get_engine_config(self, url: str) -> dict:
        """Get engine configuration based on database type"""
        config = {
            "echo": self.settings.echo,
            "pool_pre_ping": True,
        }
        
        # SQLite uses different pooling strategy
        if "sqlite" in url:
            config["connect_args"] = self.settings.get_connect_args()
            if ":memory:" in url:
                config["poolclass"] = StaticPool
            else:
                config["poolclass"] = NullPool
        else:
            # PostgreSQL, MySQL, MariaDB
            config.update({
                "pool_size": self.settings.pool_size,
                "max_overflow": self.settings.max_overflow,
                "pool_timeout": self.settings.pool_timeout,
                "pool_recycle": self.settings.pool_recycle,
                "poolclass": QueuePool,
                "connect_args": self.settings.get_connect_args(),
            })
        
        return config
    
    @property
    def engine(self) -> Engine:
        """Get or create synchronous engine"""
        if self._engine is None:
            url = self.settings.build_url(is_async=False)
            config = self._get_engine_config(url)
            self._engine = create_engine(url, **config)
            logger.info(f"[{self.name}] Sync engine created")
        return self._engine
    
    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create asynchronous engine"""
        if not self.settings.enable_async:
            raise RuntimeError(f"Async not enabled for database '{self.name}'")
        
        if self._async_engine is None:
            url = self.settings.build_url(is_async=True)
            config = self._get_engine_config(url)
            
            # Remove sync-specific poolclass
            config.pop("poolclass", None)
            
            self._async_engine = create_async_engine(url, **config)
            self._async_session_maker = async_sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info(f"[{self.name}] Async engine created")
        
        return self._async_engine
    
    @contextmanager
    def session(self) -> Iterator[Session]:
        """
        Get synchronous database session with automatic cleanup
        
        Usage:
            with connection.session() as session:
                session.execute(...)
        """
        session = Session(self.engine)
        
        try:
            logger.debug(f"[{self.name}] Session created: {id(session)}")
            yield session
            session.commit()
            logger.debug(f"[{self.name}] Session committed: {id(session)}")
        except Exception as e:
            logger.error(f"[{self.name}] Session error: {e}")
            session.rollback()
            logger.debug(f"[{self.name}] Session rolled back: {id(session)}")
            raise
        finally:
            session.close()
            logger.debug(f"[{self.name}] Session closed: {id(session)}")
    
    @asynccontextmanager
    async def async_session(self) -> AsyncIterator[AsyncSession]:
        """
        Get asynchronous database session with automatic cleanup
        
        Usage:
            async with connection.async_session() as session:
                await session.execute(...)
        """
        if self._async_session_maker is None:
            _ = self.async_engine  # Initialize
        
        async with self._async_session_maker() as session:
            try:
                logger.debug(f"[{self.name}] Async session created: {id(session)}")
                yield session
                await session.commit()
                logger.debug(f"[{self.name}] Async session committed: {id(session)}")
            except Exception as e:
                logger.error(f"[{self.name}] Async session error: {e}")
                await session.rollback()
                logger.debug(f"[{self.name}] Async session rolled back: {id(session)}")
                raise
    
    def create_tables(self) -> None:
        """Create all tables (synchronous)"""
        try:
            SQLModel.metadata.create_all(bind=self.engine)
            logger.info(f"[{self.name}] Tables created")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to create tables: {e}")
            raise
    
    async def create_tables_async(self) -> None:
        """Create all tables (asynchronous)"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info(f"[{self.name}] Tables created (async)")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to create tables (async): {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables (synchronous)"""
        try:
            SQLModel.metadata.drop_all(bind=self.engine)
            logger.warning(f"[{self.name}] Tables dropped")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to drop tables: {e}")
            raise
    
    async def drop_tables_async(self) -> None:
        """Drop all tables (asynchronous)"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
            logger.warning(f"[{self.name}] Tables dropped (async)")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to drop tables (async): {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            if self.settings.enable_async:
                async with self.async_session() as session:
                    from sqlmodel import select
                    result = await session.execute(select(1))
                    return result.scalar() == 1
            else:
                with self.session() as session:
                    from sqlmodel import select
                    result = session.execute(select(1))
                    return result.scalar() == 1
        except Exception as e:
            logger.error(f"[{self.name}] Health check failed: {e}")
            return False
    
    def dispose(self) -> None:
        """Dispose synchronous engine"""
        if self._engine:
            self._engine.dispose()
            logger.info(f"[{self.name}] Sync engine disposed")
    
    async def dispose_async(self) -> None:
        """Dispose asynchronous engine"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info(f"[{self.name}] Async engine disposed")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected
    
    def __repr__(self) -> str:
        return f"DatabaseConnection(name='{self.name}', type={self.settings.type})"