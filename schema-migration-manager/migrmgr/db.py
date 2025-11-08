"""
Database adapter layer with SqliteAdapter and MySQLAdapter.
Supports:
✅ SQLite executescript
✅ MySQL executescript (manual splitter)
✅ Transactions (MySQL auto transactions fixed)
✅ schema_versions helpers (Laravel-style)
"""

from typing import Optional


# ============================================================
# Base Adapter
# ============================================================

class DatabaseAdapter:
    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def execute(self, sql: str, params: Optional[tuple] = None):
        raise NotImplementedError

    def executescript(self, sql_script: str):
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


# ============================================================
# SQLITE ADAPTER
# ============================================================

class SqliteAdapter(DatabaseAdapter):
    def __init__(self, url: str):
        if url.startswith('sqlite:///'):
            self.path = url[len('sqlite:///'):]
        else:
            self.path = url
        self.conn = None

    def connect(self):
        import sqlite3
        self.conn = sqlite3.connect(self.path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            try: self.conn.close()
            except: pass
            self.conn = None

    def execute(self, sql: str, params: Optional[tuple] = None):
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        return cur

    def executescript(self, sql_script: str):
        return self.conn.executescript(sql_script)

    # -------------------------------
    # Migration helper methods (sqlite)
    # -------------------------------
    def has_applied(self, migration_id: str) -> bool:
        # be tolerant of older schema that used 'version' column
        try:
            cur = self.execute("PRAGMA table_info(schema_versions)")
            cols = [r[1] for r in cur.fetchall()]
            try: cur.close()
            except: pass
        except Exception:
            cols = []

        id_col = 'migration_id' if 'migration_id' in cols else ('version' if 'version' in cols else 'migration_id')
        row = self.fetchone(
            f"SELECT 1 FROM schema_versions WHERE {id_col} = ?",
            (migration_id,)
        )
        return row is not None

    def get_applied(self, migration_id: str):
        try:
            cur = self.execute("PRAGMA table_info(schema_versions)")
            cols = [r[1] for r in cur.fetchall()]
            try: cur.close()
            except: pass
        except Exception:
            cols = []

        id_col = 'migration_id' if 'migration_id' in cols else ('version' if 'version' in cols else 'migration_id')

        row = self.fetchone(
            f"SELECT * FROM schema_versions WHERE {id_col} = ?",
            (migration_id,)
        )
        if row is None:
            return None
        # sqlite3.Row -> behave like dict
        try:
            return dict(row)
        except Exception:
            # fallback tuple
            return row

    def record_applied(self,
                       migration_id: str,
                       filename: str,
                       checksum: str,
                       applied_by: Optional[str] = None,
                       down_filename: Optional[str] = None):
        """Record an applied migration into schema_versions (SQLite).

        This explicitly inserts the canonical set of columns so NOT NULL
        constraints are satisfied.
        """
        sql = """
        INSERT INTO schema_versions
            (migration_id, filename, checksum, applied_by, down_filename)
        VALUES (?, ?, ?, ?, ?)
        """
        self.execute(sql, (migration_id, filename, checksum, applied_by, down_filename))
        self.commit()

    def remove_record(self, migration_id: str):
        try:
            cur = self.execute("PRAGMA table_info(schema_versions)")
            cols = [r[1] for r in cur.fetchall()]
            try: cur.close()
            except: pass
        except Exception:
            cols = []

        id_col = 'migration_id' if 'migration_id' in cols else ('version' if 'version' in cols else 'migration_id')
        self.execute(
            f"DELETE FROM schema_versions WHERE {id_col} = ?",
            (migration_id,)
        )
        self.commit()

    def fetchone(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def fetchall(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def begin(self):
        self.execute("BEGIN IMMEDIATE")

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()


# ============================================================
# MYSQL ADAPTER (FINAL, FIXED)
# ============================================================

class MySQLAdapter(DatabaseAdapter):
    """MySQL adapter using mysql-connector-python"""
    def __init__(self, config: dict):
        self.config = config
        self.conn = None

    def connect(self):
        import mysql.connector

        cfg = {
            "user": self.config.get("user"),
            "password": self.config.get("password"),
            "host": self.config.get("host") or "127.0.0.1",
            "database": self.config.get("dbname") or self.config.get("database")
        }

        port = self.config.get("port")
        if port:
            try: cfg["port"] = int(port)
            except: cfg["port"] = port

        self.conn = mysql.connector.connect(**cfg)

        # Disable autocommit (MySQL auto-opens transaction automatically)
        self.conn.autocommit = False
        return self.conn

    def close(self):
        if self.conn:
            try: self.conn.close()
            except: pass
            self.conn = None

    def execute(self, sql: str, params: Optional[tuple] = None):
        cur = self.conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur

    # ✅ FIXED executescript (manual multi-statement execution)
    def executescript(self, sql_script: str):
        cursor = self.conn.cursor()

        statements = sql_script.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    cursor.close()
                    raise RuntimeError(f"MySQL executescript error on: {stmt}\n{e}")

        cursor.close()

    def fetchone(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def fetchall(self, sql: str, params: Optional[tuple] = None):
        cur = self.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    # ✅ FIX: MySQL SHOULD NOT start transaction manually!
    def begin(self):
        # MySQL auto-starts transaction when autocommit=False
        pass

    def commit(self):
        self.conn.commit()

    def rollback(self):
        try: self.conn.rollback()
        except: pass

    # -------------------------------
    # Migration helper methods
    # -------------------------------

    def has_applied(self, migration_id: str) -> bool:
        row = self.fetchone(
            "SELECT 1 FROM schema_versions WHERE migration_id = %s",
            (migration_id,)
        )
        return row is not None

    def get_applied(self, migration_id: str):
        row = self.fetchone(
            "SELECT * FROM schema_versions WHERE migration_id = %s",
            (migration_id,)
        )
        return dict(row) if row else None

    def record_applied(self,
                       migration_id: str,
                       filename: str,
                       checksum: str,
                       applied_by: Optional[str] = None,
                       down_filename: Optional[str] = None):
        """Record an applied migration into schema_versions (MySQL).

        Uses %s placeholder style for mysql-connector-python.
        """
        self.execute(
            """
            INSERT INTO schema_versions (migration_id, filename, checksum, applied_by, down_filename)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                migration_id,
                filename,
                checksum,
                applied_by,
                down_filename,
            )
        )
        self.commit()

    def remove_record(self, migration_id: str):
        self.execute(
            "DELETE FROM schema_versions WHERE migration_id = %s",
            (migration_id,)
        )
        self.commit()
