# db.py
import mysql.connector


class MySQLAdapter:
    def __init__(self, config: dict):
        self.config = config
        self.conn = None

    def connect(self):
        self.conn = mysql.connector.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
            database=self.config["database"],
        )
        self.conn.autocommit = False
        return self.conn

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None

    def execute(self, sql: str, params=None):
        cur = self.conn.cursor(dictionary=True)
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def executescript(self, sql_script: str):
        cur = self.conn.cursor()
        for stmt in sql_script.split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)
        cur.close()

    def fetchone(self, sql: str, params=None):
        cur = self.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def fetchall(self, sql: str, params=None):
        cur = self.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def begin(self):
        # MySQL starts txn automatically when autocommit=False
        pass

    def commit(self):
        self.conn.commit()

    def rollback(self):
        try:
            self.conn.rollback()
        except:
            pass

    # --- migration helper methods ---

    def ensure_schema_versions(self):
        self.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions(
                migration_id VARCHAR(50) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_by VARCHAR(100),
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                down_filename VARCHAR(255),
                notes TEXT
            )
        """)
        self.commit()

    def get_applied_ids(self):
        rows = self.fetchall("SELECT migration_id FROM schema_versions ORDER BY applied_at")
        return [r["migration_id"] for r in rows]

    def get_applied(self, migration_id: str):
        return self.fetchone(
            "SELECT * FROM schema_versions WHERE migration_id = %s",
            (migration_id,)
        )

    def record_applied(self, *, mid, filename, checksum, user, down_filename):
        self.execute(
            """
            INSERT INTO schema_versions
            (migration_id, filename, checksum, applied_by, down_filename)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (mid, filename, checksum, user, down_filename),
        )
        self.commit()

    def remove_record(self, migration_id: str):
        self.execute("DELETE FROM schema_versions WHERE migration_id = %s", (migration_id,))
        self.commit()
