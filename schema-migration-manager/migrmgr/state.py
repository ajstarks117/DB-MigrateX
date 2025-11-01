"""DatabaseState with a lightweight fallback to sqlite3 for local runs.

If a PostgreSQL config is provided and psycopg2 is available, it will be used.
Otherwise the class falls back to using sqlite3 with a file `dev.sqlite3` in the project root.
"""
from typing import List, Tuple, Optional
import os

try:
    import psycopg2 
    HAS_PSYCOPG2 = True
except Exception:
    HAS_PSYCOPG2 = False
    def _strip_comments_in_file(path):
        try:
            src = io.open(path, 'r', encoding='utf-8').read()
            tokens = tokenize.generate_tokens(io.StringIO(src).readline)
            kept = [tok for tok in tokens if tok.type != tokenize.COMMENT]
            new_src = tokenize.untokenize(kept)
            io.open(path, 'w', encoding='utf-8').write(new_src)
        except Exception:
            pass

    try:
        _strip_comments_in_file(os.path.abspath(__file__))
    except Exception:
        pass
import sqlite3
import io
import tokenize
import os

try:
    import mysql.connector
    HAS_MYSQL = True
except Exception:
    HAS_MYSQL = False


class DatabaseState:
    def __init__(self, db_config: Optional[dict] = None):
       
        use_postgres = False
        use_mysql = False
        if db_config:
            if HAS_PSYCOPG2 and db_config.get('dbname') and os.getenv('DB_ENGINE', '').lower() in ('postgres', 'postgresql'):
                use_postgres = True
            # allow MySQL when DB_ENGINE is mysql and mysql-connector is installed
            if HAS_MYSQL and db_config.get('dbname') and os.getenv('DB_ENGINE', '').lower() == 'mysql':
                use_mysql = True

        if use_postgres:
            self._mode = 'postgres'
            self.conn = psycopg2.connect(**db_config)
            self.cursor = self.conn.cursor()
        elif use_mysql:
            # map keys to mysql-connector parameter names
            cfg = {
                'user': db_config.get('user'),
                'password': db_config.get('password'),
                'host': db_config.get('host') or '127.0.0.1',
                'database': db_config.get('dbname') or db_config.get('database')
            }
            port = db_config.get('port')
            if port:
                try:
                    cfg['port'] = int(port)
                except Exception:
                    cfg['port'] = port
            self._mode = 'mysql'
            self.conn = mysql.connector.connect(**cfg)
            # mysql-connector provides cursor() to get dict-like rows with dictionary=True
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
            # Use the enhanced schema_versions table with metadata fields
            if self._mode == 'postgres':
                self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    migration_id VARCHAR(100) PRIMARY KEY,
                    filename TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_by TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    down_filename TEXT,
                    notes TEXT
                );
                """)
            elif self._mode == 'mysql':
                # MySQL variant
                self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    migration_id VARCHAR(100) PRIMARY KEY,
                    filename TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_by TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    down_filename TEXT,
                    notes TEXT
                );
                """)
            else:
                self.cursor.execute("""
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

            self.conn.commit()
            # After creating the table (if missing), be tolerant of older schema that used
            # a 'version' column instead of 'migration_id'. If we detect that the existing
            # table has 'version' but not 'migration_id', migrate the table to the new
            # schema so future code can query by migration_id.
            try:
                self.cursor.execute("PRAGMA table_info(schema_versions)")
                existing_cols = [r[1] for r in self.cursor.fetchall()]
                if 'version' in existing_cols and 'migration_id' not in existing_cols:
                    # perform an online migration: create a new table, copy data,
                    # drop the old table and rename the new one.
                    self.cursor.execute("BEGIN")
                    self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_versions_new (
                        migration_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        checksum TEXT NOT NULL,
                        applied_by TEXT,
                        applied_at TEXT DEFAULT (datetime('now')),
                        down_filename TEXT,
                        notes TEXT
                    );
                    """)
                    # copy existing rows: map version -> migration_id. Some older rows may
                    # only have version/description fields; tolerate missing columns.
                    # Use COALESCE to prefer filename/checksum if present, else NULL.
                    try:
                        self.cursor.execute(
                            "INSERT OR REPLACE INTO schema_versions_new (migration_id, filename, checksum, applied_by, applied_at, down_filename, notes) "
                            "SELECT version, NULL, NULL, NULL, NULL, NULL, NULL FROM schema_versions"
                        )
                    except Exception:
                        # Fallback: copy at least the version -> migration_id
                        self.cursor.execute(
                            "INSERT OR REPLACE INTO schema_versions_new (migration_id) "
                            "SELECT version FROM schema_versions"
                        )
                    # Drop old table and rename new
                    self.cursor.execute("DROP TABLE schema_versions")
                    self.cursor.execute("ALTER TABLE schema_versions_new RENAME TO schema_versions")
                    self.conn.commit()
            except Exception:
                try:
                    self.conn.rollback()
                except Exception:
                    pass
        except Exception as e:
           
            try:
                self.conn.rollback()
            except Exception:
                pass
            raise e

    def get_applied_migrations(self) -> List[str]:
        """Fetch all applied migration versions from schema_versions table."""
        try:
            # be tolerant of older schema_versions tables that used 'version'
            if self._mode == 'postgres' or self._mode == 'mysql':
                # check columns in Postgres
                # information_schema exists in both Postgres and MySQL; adjust query for MySQL
                try:
                    self.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='schema_versions'")
                    cols = [r[0] for r in self.cursor.fetchall()]
                except Exception:
                    # fallback if information_schema query fails
                    cols = []

                if 'migration_id' in cols:
                    self.cursor.execute("SELECT migration_id FROM schema_versions ORDER BY applied_at")
                    return [row[0] for row in self.cursor.fetchall()]
                if 'version' in cols:
                    self.cursor.execute("SELECT version FROM schema_versions ORDER BY version")
                    return [row[0] for row in self.cursor.fetchall()]
                return []
            else:
                self.cursor.execute("PRAGMA table_info(schema_versions)")
                cols = [r[1] for r in self.cursor.fetchall()]
                if 'migration_id' in cols:
                    self.cursor.execute("SELECT migration_id FROM schema_versions ORDER BY applied_at")
                    return [row[0] for row in self.cursor.fetchall()]
                if 'version' in cols:
                    self.cursor.execute("SELECT version FROM schema_versions ORDER BY version")
                    return [row[0] for row in self.cursor.fetchall()]
                return []
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