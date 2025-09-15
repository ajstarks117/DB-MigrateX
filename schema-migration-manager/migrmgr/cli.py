import click
from .state import DatabaseState
from .parser import MigrationParser
from .planner import MigrationPlanner
from .executor import MigrationExecutor
from dotenv import load_dotenv
import os

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
    parser = MigrationParser("migrations")
    planner = MigrationPlanner(state.get_applied_migrations(), parser.get_migration_files())
    executor = MigrationExecutor(db_config)

    pending = planner.get_pending_migrations()
    if not pending:
        print("No pending migrations.")
        return

    for version, sql in pending:
        executor.apply_migration(version, sql)
    
    state.close()
    executor.close()

if __name__ == "__main__":
    cli()