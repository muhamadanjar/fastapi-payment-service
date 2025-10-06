
from app.infrastructure.database.connections import MultiDatabaseManager
from app.infrastructure.database.migrations import MultiDatabaseMigrationManager


database_manager = MultiDatabaseManager()
migration_manager = MultiDatabaseMigrationManager(database_manager)
