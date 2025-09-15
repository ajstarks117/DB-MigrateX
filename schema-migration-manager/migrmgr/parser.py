import os
from typing import List, Tuple

class MigrationParser:
    def __init__(self, migrations_dir: str):
        self.migrations_dir = migrations_dir

    def get_migration_files(self) -> List[Tuple[str, str]]:
        """Get all .sql migration files sorted by version."""
        files = [f for f in os.listdir(self.migrations_dir) if f.endswith(".sql")]
        files.sort()  # Sort by version (e.g., 001_create_users.sql)
        migrations = []
        for file in files:
            with open(os.path.join(self.migrations_dir, file), 'r') as f:
                sql_content = f.read()
                migrations.append((file.split('.')[0], sql_content))
        return migrations