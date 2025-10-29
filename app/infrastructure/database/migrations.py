from typing import Dict, Optional
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import os
import logging
from app.infrastructure.database.connections import DatabaseConnection
from app.infrastructure.database.manager import db_manager, DatabaseManager
logger = logging.getLogger(__name__)

class AlembicManager:
    """Manager for Alembic migrations"""
    
    def __init__(self, db_connection: DatabaseConnection, alembic_ini_path: str = "alembic.ini"):
        self.db_connection = db_connection
        self.alembic_ini_path = alembic_ini_path
        self.alembic_cfg = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Alembic configuration"""
        if not os.path.exists(self.alembic_ini_path):
            logger.warning(f"Alembic config not found: {self.alembic_ini_path}")
            return
        
        self.alembic_cfg = Config(self.alembic_ini_path)
        # Override sqlalchemy.url with current database URL
        self.alembic_cfg.set_main_option(
            "sqlalchemy.url", 
            self.db_connection.config.get_url()
        )
        logger.info(f"Alembic initialized for database '{self.db_connection.name}'")
    
    def init(self, directory: str = "alembic"):
        """Initialize Alembic in the project"""
        if not self.alembic_cfg:
            self.alembic_cfg = Config()
            self.alembic_cfg.set_main_option(
                "sqlalchemy.url",
                self.db_connection.config.get_url()
            )
        
        command.init(self.alembic_cfg, directory)
        logger.info(f"Alembic initialized in directory: {directory}")
    
    def create_migration(self, message: str, autogenerate: bool = True):
        """Create a new migration"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        command.revision(
            self.alembic_cfg,
            message=message,
            autogenerate=autogenerate
        )
        logger.info(f"Migration created: {message}")
    
    def upgrade(self, revision: str = "head"):
        """Upgrade database to a specific revision"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        command.upgrade(self.alembic_cfg, revision)
        logger.info(f"Database upgraded to: {revision}")
    
    def downgrade(self, revision: str = "-1"):
        """Downgrade database to a specific revision"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        command.downgrade(self.alembic_cfg, revision)
        logger.info(f"Database downgraded to: {revision}")
    
    def current(self) -> Optional[str]:
        """Get current database revision"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        with self.db_connection.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            return current_rev
    
    def history(self):
        """Show migration history"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        command.history(self.alembic_cfg)
    
    def stamp(self, revision: str = "head"):
        """Stamp database with a specific revision without running migrations"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        command.stamp(self.alembic_cfg, revision)
        logger.info(f"Database stamped with revision: {revision}")
    
    def get_pending_migrations(self) -> list:
        """Get list of pending migrations"""
        if not self.alembic_cfg:
            raise RuntimeError("Alembic not initialized")
        
        script = ScriptDirectory.from_config(self.alembic_cfg)
        
        with self.db_connection.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            if current_rev is None:
                # No migration applied yet
                return [rev.revision for rev in script.walk_revisions()]
            
            # Get pending revisions
            pending = []
            for rev in script.walk_revisions(base="base", head="heads"):
                if rev.revision == current_rev:
                    break
                pending.append(rev.revision)
            
            return list(reversed(pending))


class MultiDatabaseMigrationManager:
    """Manager for migrations across multiple databases"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._alembic_managers: Dict[str, AlembicManager] = {}
    
    def add_migration_config(
        self,
        db_name: str,
        alembic_ini_path: Optional[str] = None
    ) -> AlembicManager:
        """Add Alembic configuration for a specific database"""
        db_connection = self.db_manager.get_database(db_name)
        
        if alembic_ini_path is None:
            alembic_ini_path = f"alembic_{db_name}.ini"
        
        alembic_mgr = AlembicManager(db_connection, alembic_ini_path)
        self._alembic_managers[db_name] = alembic_mgr
        
        return alembic_mgr
    
    def get_migration_manager(self, db_name: Optional[str] = None) -> AlembicManager:
        """Get Alembic manager for a specific database"""
        if db_name is None:
            db_name = self.db_manager._primary_db
        
        if db_name not in self._alembic_managers:
            return self.add_migration_config(db_name)
        
        return self._alembic_managers[db_name]
    
    def upgrade_all(self, revision: str = "head"):
        """Upgrade all databases"""
        for db_name, alembic_mgr in self._alembic_managers.items():
            logger.info(f"Upgrading database: {db_name}")
            alembic_mgr.upgrade(revision)
    
    def create_migration_all(self, message: str):
        """Create migration for all databases"""
        for db_name, alembic_mgr in self._alembic_managers.items():
            logger.info(f"Creating migration for database: {db_name}")
            alembic_mgr.create_migration(f"{db_name}_{message}")
    
    def check_pending_migrations(self) -> Dict[str, list]:
        """Check pending migrations for all databases"""
        pending = {}
        for db_name, alembic_mgr in self._alembic_managers.items():
            pending[db_name] = alembic_mgr.get_pending_migrations()
        return pending
