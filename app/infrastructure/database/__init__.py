from app.config.database import DatabaseSettings
from .manager import database_manager
import logging

logger = logging.getLogger(__name__)


def setup_from_settings():
    
    """Setup databases from Pydantic settings"""
    # Primary database
    settings = DatabaseSettings()
    primary_url = settings.get_primary_url(is_async=settings.enable_async)
    database_manager.add_database(
        name="primary",
        database_url=primary_url,
        is_primary=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        echo=settings.db_echo,
        connect_args=settings.get_connect_args(),
        enable_async=settings.enable_async,
    )
    logger.info("Primary database configured from settings")
    
    # Replica database
    if settings.replica_enabled:
        replica_url = settings.get_replica_url(is_async=settings.enable_async)
        if replica_url:
            database_manager.add_database(
                name="replica",
                database_url=replica_url,
                pool_size=settings.db_pool_size // 2,
                max_overflow=settings.db_max_overflow // 2,
                echo=False,
                connect_args=settings.get_connect_args(),
                enable_async=settings.enable_async,
            )
            logger.info("Replica database configured from settings")
    
    # Analytics database
    if settings.analytics_enabled:
        analytics_url = settings.get_analytics_url(is_async=settings.enable_async)
        if analytics_url:
            database_manager.add_database(
                name="analytics",
                database_url=analytics_url,
                pool_size=5,
                max_overflow=10,
                echo=False,
                connect_args=settings.get_connect_args(),
                enable_async=settings.enable_async,
            )
            logger.info("Analytics database configured from settings")


async def on_startup():
    """Database startup handler"""
    logger.info("Initializing database connections...")
    await database_manager.connect()


async def on_shutdown():
    """Database shutdown handler"""
    logger.info("Closing database connections...")
    await database_manager.disconnect()