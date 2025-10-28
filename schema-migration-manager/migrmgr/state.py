"""DatabaseState with a lightweight fallback to sqlite3 for local runs.

If a PostgreSQL config is provided and psycopg2 is available, it will be used.
Otherwise the class falls back to using sqlite3 with a file `dev.sqlite3` in the project root.
"""
from typing import List, Tuple, Optional
import os

try:
    import psycopg2  # type: ignore
    HAS_PSYCOPG2 = True
except Exception:
    HAS_PSYCOPG2 = False

import sqlite3


class DatabaseState:
    def __init__(self, db_config: Optional[dict] = None):
        # Determine whether to use Postgres or SQLite fallback
        use_postgres = False
        if db_config:
            # basic heuristic: require at least a dbname and psycopg2 available
            if HAS_PSYCOPG2 and db_config.get('dbname'):
                use_postgres = True

        if use_postgres:
            self._mode = 'postgres'
            self.conn = psycopg2.connect(**db_config)
            self.cursor = self.conn.cursor()
        else:
            self._mode = 'sqlite'
            db_path = os.path.join(os.getcwd(), 'dev.sqlite3')
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

        self._ensure_schema_versions_table()

    def _ensure_schema_versions_table(self):
        """Ensure the schema_versions table exists."""
        try:
            if self._mode == 'postgres':
                self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
                """)
            else:
                # sqlite accepts slightly different types but the DDL below is portable
                self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT DEFAULT (datetime('now')),
                    description TEXT
                );
                """)

            self.conn.commit()
        except Exception as e:
            # rollback only if supported
            try:
                self.conn.rollback()
            except Exception:
                pass
            raise e

    def get_applied_migrations(self) -> List[str]:
        """Fetch all applied migration versions from schema_versions table."""
        try:
            self.cursor.execute("SELECT version FROM schema_versions ORDER BY version")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            raise e

    def close(self):
        """Close database connection."""
        try:
            self.cursor.close()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass