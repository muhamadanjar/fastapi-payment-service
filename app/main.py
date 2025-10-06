from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from app.infrastructure.database import on_shutdown, on_startup, setup_from_settings
from app.interfaces.http.routes import api_router as app_router
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting up application...")
    
    # Setup database connections from .env file
    setup_from_settings()
    
    # Connect to all databases
    await on_startup()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await on_shutdown()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Payment System API",
    description="Payment system with multi-database support",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(app_router)