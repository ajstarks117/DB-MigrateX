import psycopg2
from typing import List, Tuple

class DatabaseState:
    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
        self._ensure_schema_versions_table()

    def _ensure_schema_versions_table(self):
        """Ensure the schema_versions table exists."""
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version VARCHAR(50) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
            """)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_applied_migrations(self) -> List[str]:
        """Fetch all applied migration versions from schema_versions table."""
        try:
            self.cursor.execute("SELECT version FROM schema_versions ORDER BY version")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            self.conn.rollback()
            raise e

    def close(self):
        """Close database connection."""
        self.cursor.close()
        self.conn.close()