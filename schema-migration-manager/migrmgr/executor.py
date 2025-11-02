"""Executor implementing apply/rollback with checksum, idempotency, and integrity checks."""
from pathlib import Path
import logging
import os
from typing import Optional

from .db import SqliteAdapter
from .integrity import run_pre_checks, run_post_checks

try:
    from .db import MySQLAdapter
    HAS_MYSQL_ADAPTER = True
except Exception:
    HAS_MYSQL_ADAPTER = False


class MigrationError(Exception):
    pass


class MigrationExecutor:
    def __init__(self, db_path: Optional[str] = None):
        """
        db_path may be:
        - a string path for sqlite DB file
        - a dict-like DB config (MySQL or Postgres)
        """

        # ✅ If dict → use MySQL adapter
        if isinstance(db_path, dict):
            db_conf = db_path
            if os.getenv("DB_ENGINE", "").lower() == "mysql" and HAS_MYSQL_ADAPTER:
                self.adapter = MySQLAdapter(db_conf)
            else:
                self.adapter = SqliteAdapter(str(Path.cwd() / "dev.sqlite3"))
        else:
            self.adapter = SqliteAdapter(str(db_path or Path.cwd() / "dev.sqlite3"))

        # ✅ connect to DB
        self.adapter.connect()

        # ✅ ensure schema_versions table exists
        try:
            self.adapter.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    migration_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_by TEXT,
                    applied_at TEXT DEFAULT (CURRENT_TIMESTAMP),
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

    # -----------------------------------------------------------------------------------
    # ✅ APPLY MIGRATION
    # -----------------------------------------------------------------------------------
    def apply_migration(self, migration, user: str = "cli", force: bool = False, skip_integrity: bool = False):
        mid = str(migration.id)

        # ✅ Idempotency check
        existing = self.adapter.get_applied(mid)
        if existing:
            if existing.get("checksum") == migration.checksum:
                logging.info("Migration %s already applied, skipping.", mid)
                return
            else:
                raise MigrationError(
                    f"Migration {mid} already applied but checksum changed. Fix manually."
                )

        # ✅ require down file unless forced
        if not migration.down_filename and not force:
            raise MigrationError(
                f"Missing down SQL for {mid}. Add _down.sql or use --force."
            )

        # ✅ pre integrity checks
        if not skip_integrity:
            run_pre_checks(self.adapter, migration)

        logging.info("Applying migration %s", mid)

        # ✅ Execute UP SQL
        try:
            self.adapter.begin()      # ✅ safe for sqlite + MySQL
            self.adapter.executescript(migration.up_sql)  # ✅ runs multi statements
            self.adapter.commit()
        except Exception as e:
            try: self.adapter.rollback()
            except Exception: pass
            raise MigrationError(f"Failed applying migration {mid}: {e}")

        # ✅ post checks
        if not skip_integrity:
            run_post_checks(self.adapter, migration)

        # ✅ record applied
        self.adapter.record_applied(
            id=mid,
            filename=migration.filename,
            checksum=migration.checksum,
            applied_by=user,
            down_filename=migration.down_filename,
        )

        logging.info("Migration %s applied successfully", mid)

    # -----------------------------------------------------------------------------------
    # ✅ ROLLBACK SINGLE MIGRATION
    # -----------------------------------------------------------------------------------
    def rollback_migration(self, migration_id: str):
        rec = self.adapter.get_applied(migration_id)
        if not rec:
            raise MigrationError(f"Migration {migration_id} not applied")

        down_file = rec.get("down_filename")
        if not down_file:
            raise MigrationError(f"No down SQL for migration {migration_id}")

        down_path = Path("migrations") / down_file
        if not down_path.exists():
            raise MigrationError(f"Down SQL file missing: {down_path}")

        sql = down_path.read_text(encoding="utf8")

        try:
            self.adapter.begin()
            self.adapter.executescript(sql)
            self.adapter.commit()
        except Exception as e:
            try: self.adapter.rollback()
            except Exception: pass
            raise MigrationError(f"Rollback failed for {migration_id}: {e}")

        self.adapter.remove_record(migration_id)
        logging.info("Rolled back migration %s", migration_id)

    # -----------------------------------------------------------------------------------
    # ✅ ROLLBACK TO POINT
    # -----------------------------------------------------------------------------------
    def rollback_to(self, target_id: str):
        rows = self.adapter.fetchall(
            "SELECT migration_id FROM schema_versions ORDER BY applied_at DESC"
        )

        migration_list = [r["migration_id"] if isinstance(r, dict) else r[0] for r in rows]

        for mid in migration_list:
            if mid == target_id:
                logging.info("Reached target %s; stopping rollback.", target_id)
                return

            self.rollback_migration(mid)

    # -----------------------------------------------------------------------------------
    def close(self):
        try:
            self.adapter.close()
        except Exception:
            pass
