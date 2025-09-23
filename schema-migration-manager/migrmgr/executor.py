import psycopg2

class MigrationExecutor:
    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def _generate_rollback_sql(self, version: str, sql: str) -> str:
        """Generate a basic rollback SQL based on the forward migration."""
        sql_upper = sql.upper()
        if "CREATE TABLE" in sql_upper:
            # Extract table name, ignoring IF NOT EXISTS
            parts = sql_upper.split("CREATE TABLE")
            if len(parts) > 1:
                table_def = parts[1].strip()
                table_name = table_def.split("(")[0].strip()
                return f"DROP TABLE IF EXISTS {table_name};"
        elif "ALTER TABLE" in sql_upper and "ADD COLUMN" in sql_upper:
            table_name = sql_upper.split("ALTER TABLE")[1].split()[0].strip()
            column_name = sql_upper.split("ADD COLUMN")[1].split()[0].strip()
            return f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name};"
        else:
            return f"-- WARNING: Automatic rollback not supported for this migration ({version}). Please provide a custom {version}_down.sql file."

    def apply_migration(self, version: str, sql: str, description: str = ""):
        """Execute a migration and generate/store rollback SQL."""
        try:
            self.cursor.execute(sql)
            rollback_sql = self._generate_rollback_sql(version, sql)
            self.cursor.execute(
                "INSERT INTO schema_versions (version, description, rollback_sql) VALUES (%s, %s, %s)",
                (version, description, rollback_sql)
            )
            self.conn.commit()
            print(f"Applied migration: {version}")
            # Optionally save to a file for user editing
            with open(f"{version}_down.sql", "w") as f:
                f.write(rollback_sql)
        except Exception as e:
            self.conn.rollback()
            print(f"Error applying migration {version}: {e}")
            raise

    def rollback_migration(self):
        """Rollback the last applied migration using stored rollback SQL."""
        try:
            self.cursor.execute("SELECT version, rollback_sql FROM schema_versions ORDER BY applied_at DESC LIMIT 1")
            result = self.cursor.fetchone()
            if not result:
                print("No migrations to rollback.")
                return

            last_version, rollback_sql = result
            if rollback_sql.startswith("-- WARNING"):
                print(f"Cannot auto-rollback {last_version}. Please use a custom {last_version}_down.sql file.")
                return

            self.cursor.execute(rollback_sql)
            self.cursor.execute(
                "DELETE FROM schema_versions WHERE version = %s",
                (last_version,)
            )
            self.conn.commit()
            print(f"Rolled back migration: {last_version}")
        except Exception as e:
            self.conn.rollback()
            print(f"Error rolling back migration {last_version}: {e}")
            raise

    def close(self):
        """Close database connection."""
        self.cursor.close()
        self.conn.close()