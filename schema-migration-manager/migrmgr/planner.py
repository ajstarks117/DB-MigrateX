from typing import List, Tuple

class MigrationPlanner:
    def __init__(self, applied_migrations: List[str], available_migrations: List[Tuple[str, str]]):
        self.applied_migrations = applied_migrations
        self.available_migrations = available_migrations

    def get_pending_migrations(self) -> List[Tuple[str, str]]:
        """Return migrations that haven't been applied yet."""
        applied_set = set(self.applied_migrations)
        return [(version, sql) for version, sql in self.available_migrations
                if version not in applied_set]