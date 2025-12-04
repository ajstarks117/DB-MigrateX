# migrmgr/executor.py
from db import MySQLAdapter
from config import DB_CONFIG
import pathlib


class MigrationError(Exception):
    pass


class MigrationExecutor:
    def __init__(self, _conf=None):
        self.db = MySQLAdapter(DB_CONFIG)
        self.db.connect()
        self.db.ensure_schema_versions()

    def apply_migration(self, migration, user: str = "system", force: bool = False, skip_integrity: bool = False):
        mid = str(migration.id)
        existing = self.db.get_applied(mid)
        if existing:
            if existing["checksum"] == migration.checksum:
                return
            raise MigrationError(f"Checksum mismatch for already applied migration {mid}")

        # down file optional – allow if force=True
        if not migration.down_filename and not force:
            raise MigrationError(f"Missing down file for {mid}, use force=True to apply")

        try:
            self.db.begin()
            self.db.executescript(migration.up_sql)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise MigrationError(f"Failed applying {mid}: {e}")

        self.db.record_applied(
            mid=mid,
            filename=migration.filename,
            checksum=migration.checksum,
            user=user,
            down_filename=migration.down_filename,
        )

    def rollback_migration(self, migration, user: str = "system"):
        if not migration.down_filename:
            raise MigrationError("No down file specified")

        p = pathlib.Path("migrations") / migration.down_filename
        if not p.exists():
            raise MigrationError(f"Down SQL not found: {p}")

        sql = p.read_text(encoding="utf8")
        try:
            self.db.begin()
            self.db.executescript(sql)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise MigrationError(f"Rollback failed: {e}")

        self.db.remove_record(migration.id)

    def close(self):
        self.db.close()
