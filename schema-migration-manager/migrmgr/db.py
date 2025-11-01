"""Database adapter layer with a SqliteAdapter implementation."""
from typing import Any, List, Optional


class DatabaseAdapter:
    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        raise NotImplementedError

    def fetchone(self, sql: str, params: Optional[tuple] = None):
        raise NotImplementedError

    def fetchall(self, sql: str, params: Optional[tuple] = None):
        raise NotImplementedError

    def begin(self):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def rollback(self):
        raise NotImplementedError

    def lock_for_migrations(self):
        raise NotImplementedError

    def unlock_for_migrations(self):
        raise NotImplementedError


class SqliteAdapter(DatabaseAdapter):
    def __init__(self, url: str):
       
        if url.startswith('sqlite:///'):
            self.path = url[len('sqlite:///'):]
        else:
            self.path = url
        self.conn = None
        self._lock_acquired = False

    def connect(self):
        import sqlite3
        
        self.conn = sqlite3.connect(self.path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        # ensure schema_versions uses the newer 'migration_id' column if needed
        try:
            self._ensure_schema_versions_table()
        except Exception:
            # non-fatal: leave as-is
            pass
        return self.conn

    def _ensure_schema_versions_table(self):
        """Ensure schema_versions has 'migration_id'. If an older table with
        'version' exists, migrate it to the new schema by creating a new table,
        copying data (version -> migration_id) and replacing the old table.
        """
        cur = self.conn.cursor()
        try:
            cur.execute("PRAGMA table_info(schema_versions)")
            rows = cur.fetchall()
            cols = [r[1] for r in rows]
            if 'version' in cols and 'migration_id' not in cols:
                # create new table
                cur.execute('BEGIN')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS schema_versions_new (
                        migration_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        checksum TEXT NOT NULL,
                        applied_by TEXT,
                        applied_at TEXT DEFAULT (datetime('now')),
                        down_filename TEXT,
                        notes TEXT
                    );
                ''')
                # Try to copy minimal data: map version -> migration_id
                try:
                    cur.execute(
                        "INSERT OR REPLACE INTO schema_versions_new (migration_id, filename, checksum, applied_by, applied_at, down_filename, notes) "
                        "SELECT version, NULL, NULL, NULL, NULL, NULL, NULL FROM schema_versions"
                    )
                except Exception:
                    cur.execute(
                        "INSERT OR REPLACE INTO schema_versions_new (migration_id) SELECT version FROM schema_versions"
                    )
                cur.execute('DROP TABLE schema_versions')
                cur.execute('ALTER TABLE schema_versions_new RENAME TO schema_versions')
                self.conn.commit()
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def execute(self, sql: str, params: Optional[tuple] = None):
        cur = self.conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def executescript(self, sql_script: str):
       
        return self.conn.executescript(sql_script)

    def fetchone(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        return cur.fetchone()

    def fetchall(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        return cur.fetchall()

    def begin(self):
       
        self.execute('BEGIN IMMEDIATE')

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def lock_for_migrations(self):
       
        self.execute('CREATE TABLE IF NOT EXISTS migrations_lock (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
        try:
            self.begin()
            
            self.execute("INSERT INTO migrations_lock (id, name) VALUES (1, 'lock')")
            self._lock_acquired = True
            self.commit()
        except Exception:
            try:
                self.rollback()
            except Exception:
                pass
            self._lock_acquired = False

    def unlock_for_migrations(self):
        if not self._lock_acquired:
            return
        try:
            self.execute("DELETE FROM migrations_lock WHERE id = 1")
            self._lock_acquired = False
        except Exception:
            pass

    # Helper methods for migration tracking
    def has_applied(self, migration_id: str) -> bool:
        # Be tolerant of older schema that used 'version' instead of 'migration_id'
        cur = self.conn.execute("PRAGMA table_info(schema_versions)")
        cols = [c[1] for c in cur.fetchall()]
        if 'migration_id' in cols:
            row = self.fetchone("SELECT 1 FROM schema_versions WHERE migration_id = ?", (migration_id,))
            return row is not None
        if 'version' in cols:
            row = self.fetchone("SELECT 1 FROM schema_versions WHERE version = ?", (migration_id,))
            return row is not None
        return False

    def get_applied(self, migration_id: str):
        # tolerate old schema using 'version' column
        cur = self.conn.execute("PRAGMA table_info(schema_versions)")
        cols = [c[1] for c in cur.fetchall()]
        if 'migration_id' in cols:
            row = self.fetchone("SELECT * FROM schema_versions WHERE migration_id = ?", (migration_id,))
            if row is None:
                return None
            try:
                return dict(row)
            except Exception:
                cols = [c[0] for c in self.conn.execute('PRAGMA table_info(schema_versions)')]
                return {cols[i]: row[i] for i in range(len(row))}
        if 'version' in cols:
            # map legacy 'version' row to current shape
            row = self.fetchone("SELECT * FROM schema_versions WHERE version = ?", (migration_id,))
            if row is None:
                return None
            try:
                r = dict(row)
            except Exception:
                cols = [c[0] for c in self.conn.execute('PRAGMA table_info(schema_versions)')]
                r = {cols[i]: row[i] for i in range(len(row))}
            # Build a compatible dict
            out = {
                'migration_id': r.get('version'),
                'filename': r.get('description') or r.get('filename'),
                'checksum': r.get('checksum'),
                'applied_by': r.get('applied_by'),
                'down_filename': r.get('down_filename'),
                'applied_at': r.get('applied_at'),
                'notes': r.get('notes'),
            }
            return out
        return None

    def record_applied(self, **fields):
        """Insert a record into schema_versions.

        Expected keys: id, filename, checksum, applied_by, down_filename
        """
        # adapt to existing schema
        cur = self.conn.execute("PRAGMA table_info(schema_versions)")
        cols = [c[1] for c in cur.fetchall()]
        if 'migration_id' in cols:
            self.execute("""
                INSERT INTO schema_versions (migration_id, filename, checksum, applied_by, down_filename)
                VALUES (?, ?, ?, ?, ?)
            """, (fields.get('id'), fields.get('filename'), fields.get('checksum'), fields.get('applied_by'), fields.get('down_filename')))
            self.commit()
            return
        if 'version' in cols:
            # legacy table: try to insert version and description if present
            if 'description' in cols:
                self.execute("INSERT INTO schema_versions (version, description) VALUES (?, ?)", (fields.get('id'), fields.get('filename')))
                self.commit()
                return
            # fallback: cannot record
            raise RuntimeError('schema_versions table uses legacy layout; cannot record new migration')

    def remove_record(self, migration_id: str):
        cur = self.conn.execute("PRAGMA table_info(schema_versions)")
        cols = [c[1] for c in cur.fetchall()]
        if 'migration_id' in cols:
            self.execute("DELETE FROM schema_versions WHERE migration_id = ?", (migration_id,))
            self.commit()
            return
        if 'version' in cols:
            self.execute("DELETE FROM schema_versions WHERE version = ?", (migration_id,))
            self.commit()
            return
        # nothing to do
        return


class MySQLAdapter(DatabaseAdapter):
    """A lightweight MySQL adapter using mysql-connector-python.

    This provides the minimal interface used by the executor/state:
    - connect/close
    - execute/executescript/fetchone/fetchall
    - transaction control begin/commit/rollback
    - simple lock table semantics for migrations
    - helpers: has_applied, get_applied, record_applied, remove_record
    """
    def __init__(self, config: str | dict):
        # config may be a DSN/path-like string or a dict with keys matching
        # DB config (dbname, user, password, host, port)
        self.config = config
        self.conn = None
        self._lock_acquired = False

    def connect(self):
        try:
            import mysql.connector
        except Exception as e:
            raise RuntimeError('mysql-connector not installed or import failed') from e

        cfg = {}
        if isinstance(self.config, dict):
            cfg['user'] = self.config.get('user')
            cfg['password'] = self.config.get('password')
            cfg['host'] = self.config.get('host') or '127.0.0.1'
            port = self.config.get('port')
            if port:
                try:
                    cfg['port'] = int(port)
                except Exception:
                    cfg['port'] = port
            # mysql-connector expects `database` not `dbname`
            cfg['database'] = self.config.get('dbname') or self.config.get('database')
        else:
            # fall back to a file path -> use sqlite instead (not supported here)
            raise RuntimeError('MySQLAdapter requires a dict config')

        self.conn = mysql.connector.connect(**cfg)
        # ensure autocommit off, we'll manage transactions
        try:
            self.conn.autocommit = False
        except Exception:
            pass
        return self.conn

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def execute(self, sql: str, params: Optional[tuple] = None):
        cur = self.conn.cursor(dictionary=True)
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def executescript(self, sql_script: str):
        # mysql-connector supports multi-statement execution via cursor.execute(..., multi=True)
        cur = self.conn.cursor()
        try:
            for result in cur.execute(sql_script, multi=True):
                pass
            return cur
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def fetchone(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        row = cur.fetchone()
        try:
            cur.close()
        except Exception:
            pass
        return row

    def fetchall(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        rows = cur.fetchall()
        try:
            cur.close()
        except Exception:
            pass
        return rows

    def begin(self):
        try:
            # explicit transaction start
            self.conn.start_transaction()
        except Exception:
            pass

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def lock_for_migrations(self):
        self.execute('CREATE TABLE IF NOT EXISTS migrations_lock (id INT PRIMARY KEY, name VARCHAR(255) UNIQUE)')
        try:
            self.begin()
            self.execute("INSERT INTO migrations_lock (id, name) VALUES (1, 'lock')")
            self._lock_acquired = True
            self.commit()
        except Exception:
            try:
                self.rollback()
            except Exception:
                pass
            self._lock_acquired = False

    def unlock_for_migrations(self):
        if not self._lock_acquired:
            return
        try:
            self.execute('DELETE FROM migrations_lock WHERE id = %s', (1,))
            self._lock_acquired = False
        except Exception:
            pass

    # Helper methods for migration tracking
    def has_applied(self, migration_id: str) -> bool:
        row = self.fetchone("SELECT 1 FROM schema_versions WHERE migration_id = %s", (migration_id,))
        return row is not None

    def get_applied(self, migration_id: str):
        row = self.fetchone("SELECT * FROM schema_versions WHERE migration_id = %s", (migration_id,))
        if row is None:
            return None
        # row is a dict (dictionary=True on cursor)
        return dict(row)

    def record_applied(self, **fields):
        self.execute(
            """
            INSERT INTO schema_versions (migration_id, filename, checksum, applied_by, down_filename)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (fields.get('id'), fields.get('filename'), fields.get('checksum'), fields.get('applied_by'), fields.get('down_filename'))
        )
        self.commit()

    def remove_record(self, migration_id: str):
        self.execute("DELETE FROM schema_versions WHERE migration_id = %s", (migration_id,))
        self.commit()
