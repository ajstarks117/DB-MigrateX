"""Migration executor with sqlite3 fallback for local runs."""
from typing import Optional
import os

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except Exception:
    HAS_PSYCOPG2 = False

from .db import SqliteAdapter


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
            self.adapter = SqliteAdapter(db_path)
            self.conn = self.adapter.connect()
            self.param_style = '?'

    def apply_migration(self, version: str, sql: str, description: str = ""):
        """Execute a migration and mark it as applied."""
        try:
            if self._mode == 'sqlite':
                
                self.adapter.executescript(sql)
                
                self.adapter.execute('CREATE TABLE IF NOT EXISTS schema_versions (version TEXT PRIMARY KEY, description TEXT)')
                self.adapter.execute('INSERT INTO schema_versions (version, description) VALUES (?, ?)', (version, description))
                
                self.conn.commit()
            else:
                self.cursor.execute(sql)
                self.cursor.execute('INSERT INTO schema_versions (version, description) VALUES (%s, %s)', (version, description))
                self.conn.commit()

            print(f"Applied migration: {version}")
        except Exception as e:
            try:
                if self._mode == 'sqlite':
                    self.conn.rollback()
                else:
                    self.conn.rollback()
            except Exception:
                pass
            print(f"Error applying migration {version}: {e}")
            raise

    def close(self):
        """Close database connection."""
        try:
            if self._mode == 'sqlite':
                self.adapter.close()
            else:
                self.cursor.close()
                self.conn.close()
        except Exception:
            pass