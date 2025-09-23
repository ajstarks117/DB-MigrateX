from typing import List, Tuple

class MigrationPlanner:
    def __init__(self, applied_migrations: List[str], available_migrations: List[Tuple[str, str]]):
        self.applied_migrations = applied_migrations
        self.available_migrations = available_migrations

    def _parse_dependencies(self, sql: str) -> List[str]:
        """Parse SQL to detect table dependencies (e.g., FOREIGN KEY references)."""
        dependencies = []
        if "REFERENCES" in sql.upper():
            # Simple heuristic: Look for REFERENCES and extract table name
            start_idx = sql.upper().find("REFERENCES") + len("REFERENCES")
            end_idx = sql.find("(", start_idx)
            if end_idx == -1:
                end_idx = sql.find(" ", start_idx)
            if start_idx < end_idx:
                dep_table = sql[start_idx:end_idx].strip()
                dependencies.append(dep_table)
        return dependencies

    def get_pending_migrations(self) -> List[Tuple[str, str]]:
        """Return migrations that haven't been applied yet, sorted by dependencies."""
        applied_set = set(self.applied_migrations)
        pending = [(version, sql) for version, sql in self.available_migrations if version not in applied_set]
        
        # Sort based on dependencies
        sorted_migrations = []
        while pending:
            for i, (version, sql) in enumerate(pending):
                deps = self._parse_dependencies(sql)
                if all(dep not in [v for v, _ in pending] for dep in deps):
                    sorted_migrations.append((version, sql))
                    pending.pop(i)
                    break
            else:
                raise ValueError(f"Circular dependency or unresolvable migration: {pending}")
        return sorted_migrations

    def validate_migration(self, version: str, sql: str, state: 'DatabaseState') -> bool:
        """Validate if the migration can be applied based on current schema."""
        if "CREATE TABLE" in sql.upper():
            table_name = sql.upper().split("CREATE TABLE")[1].split("(")[0].strip()
            state.cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                (table_name.lower(),)
            )
            if state.cursor.fetchone()[0]:
                print(f"Warning: Table {table_name} already exists for migration {version}. Skipping.")
                return False
        return True