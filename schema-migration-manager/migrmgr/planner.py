from typing import List, Dict, Iterable
from collections import defaultdict, deque


class MigrationPlanError(Exception):
    """Raised when a migration plan cannot be built (cycles or missing deps)."""
    pass


class MigrationPlanner:
    """Build a migration plan (topological sort by requires) and detect cycles.

    Expects migrations to be iterable of objects with `.id` and `.requires`.
    """
    def __init__(self, applied: Iterable[str] = None):
        self.applied = set(applied or [])

    def build_plan(self, migrations: List) -> List:
        # map id -> migration
        nodes: Dict[str, object] = {m.id: m for m in migrations}

        # build graph edges: require -> id
        incoming = {mid: 0 for mid in nodes}
        adj = defaultdict(list)
        for m in migrations:
            for r in (m.requires or []):
                if r in nodes:
                    adj[r].append(m.id)
                    incoming[m.id] += 1
                else:
                  
                    continue

     
        q = deque([n for n, deg in incoming.items() if deg == 0 and n not in self.applied])
        ordered = []
        while q:
            nid = q.popleft()
            ordered.append(nodes[nid])
            for neigh in adj.get(nid, []):
                incoming[neigh] -= 1
                if incoming[neigh] == 0 and neigh not in self.applied:
                    q.append(neigh)

       
        cycles = [n for n, deg in incoming.items() if deg > 0 and n not in self.applied]
        if cycles:
            raise MigrationPlanError(f"Cycle detected or unresolved dependencies among: {', '.join(cycles)}")

        return ordered

    def build_graph_text(self, migrations: List) -> str:
        lines = []
        for m in migrations:
            deps = ', '.join(m.requires) if m.requires else ''
            lines.append(f"{m.id}: {deps}")
        return '\n'.join(lines)
