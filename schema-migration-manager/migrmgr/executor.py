import psycopg2

class MigrationExecutor:
    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def apply_migration(self, version: str, sql: str, description: str = ""):
        """Execute a migration and mark it as applied."""
        try:
            self.cursor.execute(sql)
            self.cursor.execute(
                "INSERT INTO schema_versions (version, description) VALUES (%s, %s)",
                (version, description)
            )
            self.conn.commit()
            print(f"Applied migration: {version}")
        except Exception as e:
            self.conn.rollback()
            print(f"Error applying migration {version}: {e}")
            raise

    def close(self):
        """Close database connection."""
        self.cursor.close()
        self.conn.close()