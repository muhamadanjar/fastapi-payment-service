# config/database.py
from enum import Enum
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MARIADB = "mariadb"


class DatabaseSettings(BaseSettings):
    """Database configuration from environment variables"""
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_prefix="DB_"
    )
    
    # Primary Database
    type: DatabaseType = Field(default=DatabaseType.POSTGRESQL)
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="postgres")
    password: str = Field(default=os.environ.get('DB_PASSWORD'))
    name: str = Field(default=os.environ.get('DB_NAME'))
    
    # SQLite specific
    path: Optional[str] = Field(default="./app.db")
    
    # Connection pool
    pool_size: int = Field(default=10, ge=1)
    max_overflow: int = Field(default=20, ge=0)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=-1)
    echo: bool = Field(default=False)
    
    # Additional settings
    connect_timeout: int = Field(default=10)
    charset: str = Field(default="utf8mb4")
    
    # Async support
    enable_async: bool = Field(default=False)
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    def build_url(self, is_async: bool = False) -> str:
        """Build database URL string"""
        if self.type == DatabaseType.SQLITE:
            path = self.path if self.path else "./app.db"
            driver = "sqlite+aiosqlite" if is_async else "sqlite"
            return f"{driver}:///{path}"
        
        elif self.type == DatabaseType.POSTGRESQL:
            port = self.port or 5432
            driver = "postgresql+asyncpg" if is_async else "postgresql+psycopg2"
            return f"{driver}://{self.user}:{self.password}@{self.host}:{port}/{self.name}"
        
        elif self.type in (DatabaseType.MYSQL, DatabaseType.MARIADB):
            port = self.port or 3306
            driver = "mysql+aiomysql" if is_async else "mysql+pymysql"
            return f"{driver}://{self.user}:{self.password}@{self.host}:{port}/{self.name}?charset={self.charset}"
        
        raise ValueError(f"Unsupported database type: {self.type}")
    
    def get_connect_args(self) -> dict:
        """Get connection arguments based on database type"""
        if self.type == DatabaseType.SQLITE:
            return {"check_same_thread": False}
        
        elif self.type == DatabaseType.POSTGRESQL:
            return {"connect_timeout": self.connect_timeout}
        
        elif self.type in (DatabaseType.MYSQL, DatabaseType.MARIADB):
            return {
                "connect_timeout": self.connect_timeout,
                "charset": self.charset,
            }
        
        return {}


# Preset configurations for different databases
class ReplicaSettings(DatabaseSettings):
    """Replica database settings"""
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_prefix="REPLICA_DB_"
    )


class AnalyticsSettings(DatabaseSettings):
    """Analytics database settings"""
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_prefix="ANALYTICS_DB_"
    )


class CacheSettings(DatabaseSettings):
    """Cache database settings (e.g., Redis via SQLAlchemy)"""
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_prefix="CACHE_DB_"
    )