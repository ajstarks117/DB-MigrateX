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
        return self.conn

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
