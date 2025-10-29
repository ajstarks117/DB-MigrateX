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
@click.option('--skip-integrity', is_flag=True, help='Skip pre/post integrity checks')
@click.option('--force', is_flag=True, help='Force apply even if down file is missing')
@click.option('--rollback-to', help='Rollback applied migrations down to given migration id')
def migrate(migrations_dir, dry_run, skip_integrity, force, rollback_to):
    """Apply all pending migrations or show plan; supports rollback-to target."""

    migrations = migration_parser.parse_migrations(migrations_dir)

    state = DatabaseState(db_config)
    # For dry-run we don't consult the DB state (show what would be applied from scratch)
    if dry_run:
        applied = []
    else:
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

    executor = MigrationExecutor(db_config)
    try:
        if rollback_to:
            executor.rollback_to(rollback_to)
            return

        if not plan:
            click.echo('No pending migrations.')
            state.close()
            return

        # who is applying
        import getpass
        user = getpass.getuser()

        for m in plan:
            executor.apply_migration(m, user=user, force=force, skip_integrity=skip_integrity)
    finally:
        executor.close()
        state.close()


if __name__ == '__main__':
    cli()