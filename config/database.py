
from typing import Generator, Optional, Dict

class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MARIADB = "mariadb"


class DatabaseConfig:
    """Database configuration class"""
    
    def __init__(
        self,
        db_type: DatabaseType,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        # SQLite specific
        db_path: Optional[str] = None,
        # Connection pool settings
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        # Additional options
        connect_args: Optional[Dict] = None,
    ):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.connect_args = connect_args or {}

    def get_url(self) -> str:
        """Generate database URL based on configuration"""
        if self.db_type == DatabaseType.SQLITE:
            if not self.db_path:
                raise ValueError("db_path is required for SQLite")
            return f"sqlite:///{self.db_path}"
        
        elif self.db_type == DatabaseType.POSTGRESQL:
            port = self.port or 5432
            driver = "postgresql+psycopg2"
            return f"{driver}://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
        
        elif self.db_type == DatabaseType.MYSQL:
            port = self.port or 3306
            driver = "mysql+pymysql"
            return f"{driver}://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
        
        elif self.db_type == DatabaseType.MARIADB:
            port = self.port or 3306
            driver = "mysql+pymysql"
            return f"{driver}://{self.username}:{self.password}@{self.host}:{port}/{self.database}"
        
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")