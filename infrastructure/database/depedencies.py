from typing import Generator, Optional

from sqlmodel import Session


def get_db(db_name: Optional[str] = None) -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database session
    
    Usage:
        # Primary database (default)
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            # use primary db session
            pass
        
        # Specific database
        @app.get("/analytics")
        def get_analytics(db: Session = Depends(get_analytics_db)):
            # use analytics db
            pass
    """
    session = db_manager.get_session(db_name)
    try:
        yield session
    finally:
        session.close()


def get_primary_db() -> Generator[Session, None, None]:
    """
    Get primary database session (alias for get_db)
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_primary_db)):
            pass
    """
    return get_db(None)


def get_analytics_db() -> Generator[Session, None, None]:
    """
    Get analytics database session
    
    Usage:
        @app.get("/analytics")
        def get_analytics(db: Session = Depends(get_analytics_db)):
            pass
    """
    return get_db("analytics")


def get_replica_db() -> Generator[Session, None, None]:
    """
    Get replica database session (for read-only queries)
    
    Usage:
        @app.get("/reports")
        def get_reports(db: Session = Depends(get_replica_db)):
            pass
    """
    return get_db("replica")


def create_db_dependency(db_name: str):
    """
    Factory function to create custom database dependency
    
    Usage:
        get_custom_db = create_db_dependency("custom_db")
        
        @app.get("/custom")
        def custom_endpoint(db: Session = Depends(get_custom_db)):
            pass
    """
    def dependency() -> Generator[Session, None, None]:
        return get_db(db_name)
    return dependency