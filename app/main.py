from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from app.config.database import AnalyticsSettings, DatabaseSettings, ReplicaSettings
from app.infrastructure.database.manager import db_manager
from app.interfaces.http.routes import api_router as app_router
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting up application...")
    
    # Setup database connections from .env file
    """Application lifespan manager"""
    
    # Register databases
    db_manager.register(
        name="primary",
        settings=DatabaseSettings(),
        is_primary=True
    )
    
    db_manager.register(
        name="replica",
        settings=ReplicaSettings()
    )
    
    db_manager.register(
        name="analytics",
        settings=AnalyticsSettings()
    )
    
    # Initialize all databases
    await db_manager.initialize()


    yield

    # Shutdown
    await db_manager.shutdown()


app = FastAPI(
    title="Payment System API",
    description="Payment system with multi-database support",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(app_router)