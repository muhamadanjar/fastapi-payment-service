from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from app.infrastructure.database import on_shutdown, on_startup, setup_from_settings
from domain.entity.product import Product

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