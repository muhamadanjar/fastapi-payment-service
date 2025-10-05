import asyncio
from typing import AsyncIterator, Dict, Iterator, Optional
from sqlalchemy import Engine, StaticPool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from app.core.exceptions import DatabaseError
from config.database import DatabaseConfig, DatabaseType
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import asynccontextmanager, contextmanager
import logging

logger = logging.getLogger(__name__)



class DatabaseConnection:
    """Single database connection manager with sync and async support"""
    
    def __init__(
        self,
        name: str,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        connect_args: Optional[dict] = None,
        enable_async: bool = False,
    ):
        self.name = name
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.connect_args = connect_args or {}
        self.enable_async = enable_async
        
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
        self._is_connected = False
        self._lock = asyncio.Lock()
    
    def _get_engine_config(self) -> dict:
        """Get engine configuration"""
        config = {
            "echo": self.echo,
            "pool_pre_ping": True,
        }
        
        # SQLite uses different pooling
        if "sqlite" in self.database_url:
            config["connect_args"] = {"check_same_thread": False, **self.connect_args}
            if ":memory:" in self.database_url:
                config["poolclass"] = StaticPool
            else:
                config["poolclass"] = NullPool
        else:
            config.update({
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "poolclass": QueuePool,
                "connect_args": self.connect_args,
            })
        
        return config
    
    def _create_sync_engine(self) -> Engine:
        """Create synchronous database engine"""
        try:
            config = self._get_engine_config()
            engine = create_engine(self.database_url, **config)
            logger.info(f"Sync engine created for '{self.name}': {self.database_url}")
            return engine
        except Exception as e:
            logger.error(f"Failed to create sync engine for '{self.name}': {e}")
            raise DatabaseError(f"Sync engine creation failed: {e}")
    
    def _create_async_engine(self) -> AsyncEngine:
        """Create asynchronous database engine"""
        try:
            config = self._get_engine_config()
            # Remove sync-specific configs
            config.pop("poolclass", None)
            
            engine = create_async_engine(self.database_url, **config)
            logger.info(f"Async engine created for '{self.name}': {self.database_url}")
            return engine
        except Exception as e:
            logger.error(f"Failed to create async engine for '{self.name}': {e}")
            raise DatabaseError(f"Async engine creation failed: {e}")
    
    def get_engine(self) -> Engine:
        """Get or create synchronous engine"""
        if self._engine is None:
            self._engine = self._create_sync_engine()
        return self._engine
    
    async def get_async_engine(self) -> AsyncEngine:
        """Get or create asynchronous engine"""
        if not self.enable_async:
            raise DatabaseError(f"Async not enabled for database '{self.name}'")
        
        if self._async_engine is None:
            async with self._lock:
                if self._async_engine is None:
                    self._async_engine = self._create_async_engine()
                    self._async_session_maker = async_sessionmaker(
                        self._async_engine,
                        class_=AsyncSession,
                        expire_on_commit=False
                    )
        return self._async_engine
    
    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Get database session with automatic cleanup"""
        engine = self.get_engine()
        session = Session(engine)
        
        try:
            logger.debug(f"Session created for '{self.name}': {id(session)}")
            yield session
            session.commit()
            logger.debug(f"Session committed for '{self.name}': {id(session)}")
        except Exception as e:
            logger.error(f"Session error for '{self.name}': {e}")
            session.rollback()
            logger.debug(f"Session rolled back for '{self.name}': {id(session)}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            session.close()
            logger.debug(f"Session closed for '{self.name}': {id(session)}")
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncIterator[AsyncSession]:
        """Get async database session with automatic cleanup"""
        if not self.enable_async:
            raise DatabaseError(f"Async not enabled for database '{self.name}'")
        
        if self._async_session_maker is None:
            await self.get_async_engine()
        
        async with self._async_session_maker() as session:
            try:
                logger.debug(f"Async session created for '{self.name}': {id(session)}")
                yield session
                await session.commit()
                logger.debug(f"Async session committed for '{self.name}': {id(session)}")
            except Exception as e:
                logger.error(f"Async session error for '{self.name}': {e}")
                await session.rollback()
                logger.debug(f"Async session rolled back for '{self.name}': {id(session)}")
                raise DatabaseError(f"Async database operation failed: {e}")
    
    def create_tables(self) -> None:
        """Create all tables (sync)"""
        try:
            engine = self.get_engine()
            SQLModel.metadata.create_all(bind=engine)
            logger.info(f"Tables created for '{self.name}'")
        except Exception as e:
            logger.error(f"Failed to create tables for '{self.name}': {e}")
            raise DatabaseError(f"Table creation failed: {e}")
    
    async def create_tables_async(self) -> None:
        """Create all tables (async)"""
        try:
            engine = await self.get_async_engine()
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info(f"Tables created (async) for '{self.name}'")
        except Exception as e:
            logger.error(f"Failed to create tables (async) for '{self.name}': {e}")
            raise DatabaseError(f"Async table creation failed: {e}")
    
    def drop_tables(self) -> None:
        """Drop all tables (sync)"""
        try:
            engine = self.get_engine()
            SQLModel.metadata.drop_all(bind=engine)
            logger.warning(f"Tables dropped for '{self.name}'")
        except Exception as e:
            logger.error(f"Failed to drop tables for '{self.name}': {e}")
            raise DatabaseError(f"Table drop failed: {e}")
    
    async def drop_tables_async(self) -> None:
        """Drop all tables (async)"""
        try:
            engine = await self.get_async_engine()
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
            logger.warning(f"Tables dropped (async) for '{self.name}'")
        except Exception as e:
            logger.error(f"Failed to drop tables (async) for '{self.name}': {e}")
            raise DatabaseError(f"Async table drop failed: {e}")
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            if self.enable_async:
                async with self.get_async_session() as session:
                    from sqlmodel import select
                    result = await session.execute(select(1))
                    return result.scalar() == 1
            else:
                with self.get_session() as session:
                    from sqlmodel import select
                    result = session.execute(select(1))
                    return result.scalar() == 1
        except Exception as e:
            logger.error(f"Health check failed for '{self.name}': {e}")
            return False
    
    def dispose(self) -> None:
        """Dispose synchronous engine"""
        if self._engine:
            self._engine.dispose()
            logger.info(f"Sync engine disposed for '{self.name}'")
    
    async def dispose_async(self) -> None:
        """Dispose asynchronous engine"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info(f"Async engine disposed for '{self.name}'")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected


# ==================== MULTI DATABASE MANAGER ====================
class MultiDatabaseManager:
    """Manager for multiple database connections"""
    
    def __init__(self):
        self._databases: Dict[str, DatabaseConnection] = {}
        self._primary_db: Optional[str] = None
        self._is_initialized = False
    
    def add_database(
        self,
        name: str,
        database_url: str,
        is_primary: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        connect_args: Optional[dict] = None,
        enable_async: bool = False,
    ) -> DatabaseConnection:
        """Add a new database connection"""
        if name in self._databases:
            raise ValueError(f"Database '{name}' already exists")
        
        db_conn = DatabaseConnection(
            name=name,
            database_url=database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo,
            connect_args=connect_args,
            enable_async=enable_async,
        )
        
        self._databases[name] = db_conn
        
        if is_primary or not self._primary_db:
            self._primary_db = name
            logger.info(f"Set '{name}' as primary database")
        
        return db_conn
    
    def get_database(self, name: Optional[str] = None) -> DatabaseConnection:
        """Get database connection by name"""
        db_name = name or self._primary_db
        
        if not db_name:
            raise ValueError("No database configured")
        
        if db_name not in self._databases:
            raise ValueError(f"Database '{db_name}' not found")
        
        return self._databases[db_name]
    
    def get_session(self, db_name: Optional[str] = None) -> Session:
        """Get database session"""
        return self.get_database(db_name).get_session()
    
    @contextmanager
    def session_scope(self, db_name: Optional[str] = None):
        """Get transactional session scope"""
        db = self.get_database(db_name)
        with db.get_session() as session:
            yield session
    
    async def connect(self) -> None:
        """Initialize all database connections"""
        if self._is_initialized:
            logger.warning("Database manager already initialized")
            return
        
        logger.info("Initializing database connections...")
        
        for name, db in self._databases.items():
            # Create tables
            if db.enable_async:
                await db.create_tables_async()
            else:
                db.create_tables()
            
            # Health check
            if not await db.health_check():
                raise DatabaseError(f"Health check failed for database '{name}'")
            
            db._is_connected = True
        
        self._is_initialized = True
        logger.info("All databases connected successfully")
    
    async def disconnect(self) -> None:
        """Close all database connections"""
        logger.info("Closing all database connections...")
        
        for db in self._databases.values():
            db.dispose()
            if db.enable_async:
                await db.dispose_async()
            db._is_connected = False
        
        self._is_initialized = False
        logger.info("All databases disconnected")
    
    def list_databases(self) -> list[str]:
        """List all registered database names"""
        return list(self._databases.keys())
    
    @property
    def is_connected(self) -> bool:
        """Check if manager is initialized"""
        return self._is_initialized


