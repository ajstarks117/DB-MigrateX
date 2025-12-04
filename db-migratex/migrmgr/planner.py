# migrmgr/planner.py
from typing import Iterable, List


class MigrationPlanner:
    def __init__(self, applied: Iterable[str] = None):
        self.applied = set(applied or [])

    def build_plan(self, migrations: List) -> List:
        # simple: filter out applied by id, keep lexicographic order
        return [m for m in migrations if m.id not in self.applied]

    def build_graph_text(self, migrations: List) -> str:
        return "\n".join(f"{m.id}: {m.filename}" for m in migrations)
