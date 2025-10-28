"""Migration executor with sqlite3 fallback for local runs."""
from typing import Optional
import os

try:
    import psycopg2  # type: ignore
    HAS_PSYCOPG2 = True
except Exception:
    HAS_PSYCOPG2 = False

import sqlite3


class MigrationExecutor:
    def __init__(self, db_config: Optional[dict] = None):
        use_postgres = False
        if db_config and HAS_PSYCOPG2 and db_config.get('dbname'):
            use_postgres = True

        if use_postgres:
            self._mode = 'postgres'
            self.conn = psycopg2.connect(**db_config)
            self.cursor = self.conn.cursor()
            self.param_style = '%s'
        else:
            self._mode = 'sqlite'
            db_path = os.path.join(os.getcwd(), 'dev.sqlite3')
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.param_style = '?'

    def apply_migration(self, version: str, sql: str, description: str = ""):
        """Execute a migration and mark it as applied."""
        try:
            # Execute the migration SQL. sqlite3 may require executing script instead of single execute
            if self._mode == 'sqlite':
                self.cursor.executescript(sql)
            else:
                self.cursor.execute(sql)

            # Insert marker into schema_versions
            if self._mode == 'sqlite':
                self.cursor.execute(
                    "INSERT INTO schema_versions (version, description) VALUES (?, ?)",
                    (version, description)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO schema_versions (version, description) VALUES (%s, %s)",
                    (version, description)
                )

            self.conn.commit()
            print(f"Applied migration: {version}")
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            print(f"Error applying migration {version}: {e}")
            raise

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