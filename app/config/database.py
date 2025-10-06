
from enum import Enum
import os
from typing import Generator, Optional, Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MARIADB = "mariadb"


class DatabaseSettings(BaseSettings):
    """Database configuration from environment variables"""
    
    model_config = SettingsConfigDict(
        # env_file=".env",
        # env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="DB_"
    )
    
    # Primary Database
    db_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL, description="Database type", env="DB_TYPE")
    db_host: str = Field(default=os.environ.get("DB_HOST"), description="Database host", env="DB_HOST")
    db_port: int = Field(default=5432, description="Database port")
    db_user: str = Field(default=os.environ.get('DB_USER'), description="Database username")
    db_password: str = Field(default=os.environ.get('DB_PASSWORD'), description="Database password")
    db_name: str = Field(default=os.environ.get('DB_NAME'), description="Database name")
    
    # SQLite specific
    db_path: Optional[str] = Field(default=None, description="SQLite database path")
    
    # Connection pool settings
    db_pool_size: int = Field(default=10, ge=1, description="Connection pool size")
    db_max_overflow: int = Field(default=20, ge=0, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    db_pool_recycle: int = Field(default=3600, ge=-1, description="Pool recycle time")
    db_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Additional connection args
    db_connect_timeout: int = Field(default=10, description="Connection timeout")
    db_charset: str = Field(default="utf8mb4", description="Database charset")
    
    # Async support
    enable_async: bool = Field(default=False, description="Enable async database support")
    
    # Replica/Secondary Database (Optional)
    replica_enabled: bool = Field(default=False, description="Enable replica database")
    replica_host: Optional[str] = Field(default=None)
    replica_port: Optional[int] = Field(default=None)
    replica_user: Optional[str] = Field(default=None)
    replica_password: Optional[str] = Field(default=None)
    replica_name: Optional[str] = Field(default=None)
    
    # Analytics Database (Optional)
    analytics_enabled: bool = Field(default=False, description="Enable analytics database")
    analytics_type: Optional[DatabaseType] = Field(default=None)
    analytics_host: Optional[str] = Field(default=None)
    analytics_port: Optional[int] = Field(default=None)
    analytics_user: Optional[str] = Field(default=None)
    analytics_password: Optional[str] = Field(default=None)
    analytics_name: Optional[str] = Field(default=None)
    
    @field_validator("db_port", "replica_port", "analytics_port")
    @classmethod
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    def _build_url(
        self,
        db_type: DatabaseType,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        db_path: Optional[str] = None,
        is_async: bool = False,
    ) -> str:
        """Build database URL"""
        if db_type == DatabaseType.SQLITE:
            if not db_path:
                db_path = "./app.db"
            if is_async:
                return f"sqlite+aiosqlite:///{db_path}"
            return f"sqlite:///{db_path}"
        
        elif db_type == DatabaseType.POSTGRESQL:
            port = port or 5432
            if is_async:
                driver = "postgresql+asyncpg"
            else:
                driver = "postgresql+psycopg2"
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"
        
        elif db_type in (DatabaseType.MYSQL, DatabaseType.MARIADB):
            port = port or 3306
            if is_async:
                driver = "mysql+aiomysql"
            else:
                driver = "mysql+pymysql"
            return f"{driver}://{username}:{password}@{host}:{port}/{database}?charset={self.db_charset}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def get_primary_url(self, is_async: bool = False) -> str:
        """Generate primary database URL"""
        return self._build_url(
            db_type=self.db_type,
            host=self.db_host,
            port=self.db_port,
            username=self.db_user,
            password=self.db_password,
            database=self.db_name,
            db_path=self.db_path,
            is_async=is_async,
        )
    
    def get_replica_url(self, is_async: bool = False) -> Optional[str]:
        """Generate replica database URL"""
        if not self.replica_enabled or not self.replica_host:
            return None
        
        return self._build_url(
            db_type=self.db_type,
            host=self.replica_host,
            port=self.replica_port or self.db_port,
            username=self.replica_user or self.db_user,
            password=self.replica_password or self.db_password,
            database=self.replica_name or self.db_name,
            is_async=is_async,
        )
    
    def get_analytics_url(self, is_async: bool = False) -> Optional[str]:
        """Generate analytics database URL"""
        if not self.analytics_enabled or not self.analytics_host:
            return None
        
        analytics_type = self.analytics_type or self.db_type
        
        return self._build_url(
            db_type=analytics_type,
            host=self.analytics_host,
            port=self.analytics_port or 5432,
            username=self.analytics_user,
            password=self.analytics_password,
            database=self.analytics_name,
            is_async=is_async,
        )
    
    def get_connect_args(self) -> dict:
        """Get connection arguments based on database type"""
        if self.db_type == DatabaseType.SQLITE:
            return {"check_same_thread": False}
        
        elif self.db_type == DatabaseType.POSTGRESQL:
            return {
                "connect_timeout": self.db_connect_timeout,
            }
        
        elif self.db_type in (DatabaseType.MYSQL, DatabaseType.MARIADB):
            return {
                "connect_timeout": self.db_connect_timeout,
                "charset": self.db_charset,
            }
        
        return {}
