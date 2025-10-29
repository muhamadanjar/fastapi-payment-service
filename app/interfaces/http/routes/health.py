import logging
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.infrastructure.database.depedencies import get_db
from app.infrastructure.database.manager import db_manager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
@router.get('/')
def get_all(db: Session = Depends(get_db)):
    try:
        # Check database connection
        with db_manager.session() as session:
            session.exec(text("SELECT 1"))
        
        # Check migration status
        # alembic_mgr = migration_manager.get_migration_manager()
        # current_rev = alembic_mgr.current()
        # pending = alembic_mgr.get_pending_migrations()
        
        return {
            "status": "healthy",
            "database": "connected",
            # "current_migration": current_rev,
            # "pending_migrations": len(pending)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }