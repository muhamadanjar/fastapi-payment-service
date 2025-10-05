from typing import Dict, Optional
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from config.database import DatabaseConfig, DatabaseType
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)



class DatabaseConnection:
    """Single database connection manager"""
    
    def __init__(self, config: DatabaseConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.engine = None
        self.session_local = None
        self._initialize()

    def _initialize(self):
        """Initialize database engine and session factory"""
        url = self.config.get_url()
        
        # Engine configuration based on database type
        engine_kwargs = {
            "echo": self.config.echo,
            "pool_pre_ping": True,  # Enable connection health checks
        }

        # SQLite uses NullPool, others use QueuePool
        if self.config.db_type == DatabaseType.SQLITE:
            engine_kwargs.update({
                "connect_args": {"check_same_thread": False, **self.config.connect_args},
                "poolclass": NullPool,
            })
        else:
            engine_kwargs.update({
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
                "poolclass": QueuePool,
                "connect_args": self.config.connect_args,
            })

        self.engine = create_engine(url, **engine_kwargs)
        self.session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=Session,
        )
        
        logger.info(f"Database '{self.name}' initialized: {self.config.db_type.value}")

    def create_tables(self):
        """Create all tables"""
        SQLModel.metadata.create_all(self.engine)
        logger.info(f"Tables created for database '{self.name}'")

    def drop_tables(self):
        """Drop all tables"""
        SQLModel.metadata.drop_all(self.engine)
        logger.info(f"Tables dropped for database '{self.name}'")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.session_local()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error in '{self.name}': {str(e)}")
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info(f"Database '{self.name}' connection closed")


class MultiDatabaseManager:
    """Manager for multiple database connections"""
    
    def __init__(self):
        self._databases: Dict[str, DatabaseConnection] = {}
        self._primary_db: Optional[str] = None

    def add_database(
        self,
        name: str,
        config: DatabaseConfig,
        is_primary: bool = False
    ) -> DatabaseConnection:
        """Add a new database connection"""
        if name in self._databases:
            raise ValueError(f"Database '{name}' already exists")
        
        db_conn = DatabaseConnection(config, name)
        self._databases[name] = db_conn
        
        if is_primary or not self._primary_db:
            self._primary_db = name
            logger.info(f"Set '{name}' as primary database")
        
        return db_conn

    def get_database(self, name: Optional[str] = None) -> DatabaseConnection:
        """Get database connection by name, defaults to primary"""
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
        with db.session_scope() as session:
            yield session

    def create_all_tables(self, db_name: Optional[str] = None):
        """Create tables for specific database or all databases"""
        if db_name:
            self.get_database(db_name).create_tables()
        else:
            for db in self._databases.values():
                db.create_tables()

    def close_all(self):
        """Close all database connections"""
        for db in self._databases.values():
            db.close()
        logger.info("All database connections closed")

    def list_databases(self) -> list[str]:
        """List all registered database names"""
        return list(self._databases.keys())
    
