import click
import os
from dotenv import load_dotenv
from . import parser as migration_parser
from .planner import MigrationPlanner
from .executor import MigrationExecutor
from .state import DatabaseState

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
@click.option('--migrations-dir', default='migrations', help='Directory with migration files')
@click.option('--dry-run', is_flag=True, help='Show planned migrations without applying')
def migrate(migrations_dir, dry_run):
    """Apply all pending migrations or show plan with --dry-run."""
  
    migrations = migration_parser.parse_migrations(migrations_dir)

    state = DatabaseState(db_config)
    applied = state.get_applied_migrations()

    planner = MigrationPlanner(applied)
    plan = planner.build_plan(migrations)

    if dry_run:
        click.echo('Planned migrations:')
        for m in plan:
            click.echo(f"- {m.id} {m.filename} (checksum={m.checksum})")
        click.echo('\nDependency graph:')
        click.echo(planner.build_graph_text(migrations))
        state.close()
        return

    if not plan:
        click.echo('No pending migrations.')
        state.close()
        return

    executor = MigrationExecutor(db_config)
    try:
        for m in plan:
            executor.apply_migration(m.id, m.up_sql, m.description or '')
    finally:
        executor.close()
        state.close()


if __name__ == '__main__':
    cli()