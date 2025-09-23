import os
import sys

# Adjust the import path if running standalone
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from migrmgr.state import DatabaseState
from migrmgr.parser import MigrationParser
from migrmgr.planner import MigrationPlanner
from migrmgr.executor import MigrationExecutor
from dotenv import load_dotenv
import click

load_dotenv()

db_config = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

@click.group()
def cli():
    pass

@cli.command()
def migrate():
    """Apply all pending migrations."""
    state = DatabaseState(db_config)
    parser = MigrationParser(os.path.join(os.path.dirname(__file__), "..", "migrations"))
    planner = MigrationPlanner(state.get_applied_migrations(), parser.get_migration_files())
    executor = MigrationExecutor(db_config)

    pending = planner.get_pending_migrations()
    if not pending:
        print("No pending migrations.")
        return

    for version, sql in pending:
        if planner.validate_migration(version, sql, state):
            executor.apply_migration(version, sql)
    
    state.close()
    executor.close()

@cli.command()
def rollback():
    """Rollback the last applied migration."""
    executor = MigrationExecutor(db_config)
    executor.rollback_migration()
    executor.close()

if __name__ == "__main__":
    cli()