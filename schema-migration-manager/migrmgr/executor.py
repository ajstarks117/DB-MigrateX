"""Executor implementing apply/rollback with checksum, idempotency, and integrity checks."""
from pathlib import Path
import logging
from typing import Optional

from .db import SqliteAdapter
from .integrity import run_pre_checks, run_post_checks


class MigrationError(Exception):
    pass


class MigrationExecutor:
    def __init__(self, db_path: Optional[str] = None):
        db_path = db_path or (Path.cwd() / 'dev.sqlite3')
        self.adapter = SqliteAdapter(str(db_path))
        # ensure connection
        self.adapter.connect()
        # ensure schema_versions exists (state._ensure_schema_versions_table should also have run)
        try:
            self.adapter.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    migration_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_by TEXT,
                    applied_at TEXT DEFAULT (datetime('now')),
                    down_filename TEXT,
                    notes TEXT
                );
            """)
            self.adapter.commit()
        except Exception:
            try:
                self.adapter.rollback()
            except Exception:
                pass

    def apply_migration(self, migration, user: str = 'cli', force: bool = False, skip_integrity: bool = False):
        """Apply a single migration object.

        migration: object with attributes id, filename, checksum, up_sql, down_filename
        """
        mid = str(migration.id)
        # idempotency / checksum checks
        existing = self.adapter.get_applied(mid)
        if existing:
            if existing.get('checksum') == migration.checksum:
                logging.info("Migration %s already applied, skipping.", mid)
                return
            else:
                raise MigrationError(
                    f"Migration {mid} already applied but checksum differs. File changed after apply — manual fix required."
                )

        if not migration.down_filename and not force:
            raise MigrationError(f"Missing down SQL for migration {mid}. Use --force to apply non-reversible migrations.")

        if not skip_integrity:
            run_pre_checks(self.adapter, migration)

        logging.info("Applying migration %s", mid)
        try:
            self.adapter.begin()
            # execute script (may contain multiple statements)
            self.adapter.executescript(migration.up_sql)
            self.adapter.commit()
        except Exception as e:
            try:
                self.adapter.rollback()
            except Exception:
                pass
            raise MigrationError(f"Failed applying migration {mid}: {e}")

        if not skip_integrity:
            run_post_checks(self.adapter, migration)

        # record applied
        self.adapter.record_applied(
            id=mid,
            filename=migration.filename,
            checksum=migration.checksum,
            applied_by=user,
            down_filename=migration.down_filename,
        )

        logging.info("Applied migration %s successfully", mid)

    def rollback_migration(self, migration_id: str):
        rec = self.adapter.get_applied(migration_id)
        if not rec or not rec.get('down_filename'):
            raise MigrationError(f"Cannot rollback {migration_id}: no down file recorded")

        down_sql_path = Path('migrations') / rec['down_filename']
        if not down_sql_path.exists():
            raise MigrationError(f"Down file for {migration_id} not found at {down_sql_path}")

        sql = down_sql_path.read_text(encoding='utf8')
        try:
            self.adapter.begin()
            self.adapter.executescript(sql)
            self.adapter.commit()
        except Exception as e:
            try:
                self.adapter.rollback()
            except Exception:
                pass
            raise MigrationError(f"Failed rollback of {migration_id}: {e}")

        self.adapter.remove_record(migration_id)
        logging.info("Rolled back migration %s", migration_id)

    def rollback_to(self, target_id: str):
        # Fetch applied migrations ordered by applied_at desc
        rows = self.adapter.fetchall("SELECT migration_id, down_filename FROM schema_versions ORDER BY applied_at DESC")
        to_rollback = []
        for r in rows:
            mid = r['migration_id'] if isinstance(r, dict) else r[0]
            to_rollback.append(mid)
            if mid == target_id:
                break

        if not to_rollback:
            logging.info("No migrations to rollback")
            return

        # rollback each in order (newest first) until target reached (target not rolled back)
        for mid in to_rollback:
            if mid == target_id:
                logging.info("Reached target %s; stopping rollback.", target_id)
                break
            self.rollback_migration(mid)

    def close(self):
        try:
            self.adapter.close()
        except Exception:
            pass