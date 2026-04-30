from contextlib import asynccontextmanager
import os
import logging
from fastapi import FastAPI
from app.config.database import AnalyticsSettings, DatabaseSettings, ReplicaSettings
from app.config.rate_limit import RateLimitSettings
from app.infrastructure.database.manager import db_manager
from app.interfaces.http.routes import api_router as app_router
from app.interfaces.http.routes import public_router
from app.interfaces.http.middleware.rate_limit import RateLimitMiddleware

# Import all models so SQLModel metadata registers all tables
import app.domain.entity.enums  # noqa: F401
import app.domain.entity.application  # noqa: F401
import app.domain.entity.product  # noqa: F401
import app.domain.entity.payments  # noqa: F401
import app.domain.entity.transactions  # noqa: F401
import app.domain.entity.payment_gateway  # noqa: F401
import app.domain.entity.voucher  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _has_env_vars(prefix: str) -> bool:
    """Check if any env vars with the given prefix exist (e.g. REPLICA_DB_*)."""
    return any(k.startswith(prefix) for k in os.environ)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting up application...")

    # Register primary database
    db_manager.register(
        name="primary",
        settings=DatabaseSettings(),
        is_primary=True
    )

    # Register replica database only if explicitly configured
    if _has_env_vars("REPLICA_DB_"):
        db_manager.register(name="replica", settings=ReplicaSettings())
        logger.info("Replica database configured")

    # Register analytics database only if explicitly configured
    if _has_env_vars("ANALYTICS_DB_"):
        db_manager.register(name="analytics", settings=AnalyticsSettings())
        logger.info("Analytics database configured")

    # Initialize all registered databases
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

app.add_middleware(RateLimitMiddleware, settings=RateLimitSettings())

app.include_router(app_router)
app.include_router(public_router)