# database/manager.py
from typing import Dict, Optional, Iterator, AsyncIterator
from contextlib import contextmanager, asynccontextmanager

from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.config.database import DatabaseSettings
from app.infrastructure.database.connections import DatabaseConnection

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Multi-database manager
    Manages multiple database connections (primary, replica, analytics, etc.)
    """
    
    def __init__(self):
        self._connections: Dict[str, DatabaseConnection] = {}
        self._primary_name: Optional[str] = None
        self._is_initialized = False
    
    def register(
        self,
        name: str,
        settings: DatabaseSettings,
        is_primary: bool = False
    ) -> DatabaseConnection:
        """
        Register a new database connection
        
        Args:
            name: Unique identifier for this database
            settings: Database configuration
            is_primary: Set as primary database (default for operations)
        
        Returns:
            DatabaseConnection instance
        """
        if name in self._connections:
            raise ValueError(f"Database '{name}' already registered")
        
        connection = DatabaseConnection(name=name, settings=settings)
        self._connections[name] = connection
        
        if is_primary or not self._primary_name:
            self._primary_name = name
            logger.info(f"Database '{name}' registered as PRIMARY")
        else:
            logger.info(f"Database '{name}' registered")
        
        return connection
    
    def get(self, name: Optional[str] = None) -> DatabaseConnection:
        """
        Get database connection by name
        
        Args:
            name: Database name. If None, returns primary database
        
        Returns:
            DatabaseConnection instance
        """
        db_name = name or self._primary_name
        
        if not db_name:
            raise RuntimeError("No database registered")
        
        if db_name not in self._connections:
            raise ValueError(f"Database '{db_name}' not found. Available: {self.list()}")
        
        return self._connections[db_name]
    
    @contextmanager
    def session(self, name: Optional[str] = None) -> Iterator[Session]:
        """
        Get synchronous database session
        
        Usage:
            with manager.session() as session:
                session.execute(...)
        """
        connection = self.get(name)
        with connection.session() as session:
            yield session
    
    @asynccontextmanager
    async def async_session(self, name: Optional[str] = None) -> AsyncIterator[AsyncSession]:
        """
        Get asynchronous database session
        
        Usage:
            async with manager.async_session() as session:
                await session.execute(...)
        """
        connection = self.get(name)
        async with connection.async_session() as session:
            yield session
    
    async def initialize(self) -> None:
        """
        Initialize all registered databases
        - Create tables
        - Run health checks
        """
        if self._is_initialized:
            logger.warning("Database manager already initialized")
            return
        
        if not self._connections:
            raise RuntimeError("No databases registered")
        
        logger.info(f"Initializing {len(self._connections)} database(s)...")
        
        for name, connection in self._connections.items():
            # Create tables
            if connection.settings.enable_async:
                await connection.create_tables_async()
            else:
                connection.create_tables()
            
            # Health check
            if not await connection.health_check():
                raise RuntimeError(f"Health check failed for database '{name}'")
            
            connection._is_connected = True
        
        self._is_initialized = True
        logger.info("All databases initialized successfully")
    
    async def shutdown(self) -> None:
        """
        Shutdown all database connections
        - Dispose engines
        - Clear connection pool
        """
        logger.info("Shutting down all databases...")
        
        for connection in self._connections.values():
            connection.dispose()
            if connection.settings.enable_async:
                await connection.dispose_async()
            connection._is_connected = False
        
        self._is_initialized = False
        logger.info("All databases shut down successfully")
    
    def list(self) -> list[str]:
        """List all registered database names"""
        return list(self._connections.keys())
    
    @property
    def primary(self) -> DatabaseConnection:
        """Get primary database connection"""
        return self.get(None)
    
    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized"""
        return self._is_initialized
    
    def __repr__(self) -> str:
        dbs = ", ".join(self.list())
        return f"DatabaseManager(databases=[{dbs}], primary='{self._primary_name}')"


# Global database manager instance
db_manager = DatabaseManager()
