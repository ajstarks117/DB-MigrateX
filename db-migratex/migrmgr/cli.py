# migrmgr/cli.py
import argparse
from .parser import parse_migrations
from .state import DatabaseState
from .planner import MigrationPlanner
from .executor import MigrationExecutor


def cmd_migrate(dry_run: bool):
    migrations = parse_migrations("migrations")
    state = DatabaseState()
    applied = state.get_applied_migrations()
    planner = MigrationPlanner(applied)
    plan = planner.build_plan(migrations)

    if dry_run:
        print("Planned migrations:")
        for m in plan:
            print(f"{m.id} - {m.filename} (down={m.down_filename})")
        state.close()
        return

    executor = MigrationExecutor()
    for m in plan:
        print(f"Applying {m.id} ...")
        executor.apply_migration(m, user="cli", force=True, skip_integrity=True)

    executor.close()
    state.close()
    print("All migrations applied.")


def main():
    parser = argparse.ArgumentParser(description="DB-MigrateX CLI")
    sub = parser.add_subparsers(dest="command")

    mig = sub.add_parser("migrate", help="Apply pending migrations")
    mig.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if args.command == "migrate":
        cmd_migrate(args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
