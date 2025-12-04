# normalizer/dependencies.py

class FunctionalDependencyDetector:
    def find_dependencies(self, rows):
        """
        very simple FD detection:
        A -> B if for every A value, all rows share same B
        """
        if not rows:
            return {}

        cols = list(rows[0].keys())
        deps = {}

        for a in cols:
            for b in cols:
                if a == b:
                    continue

                mapping = {}
                fd_holds = True

                for r in rows:
                    av = r[a]
                    bv = r[b]
                    if av in mapping and mapping[av] != bv:
                        fd_holds = False
                        break
                    mapping[av] = bv

                if fd_holds:
                    deps.setdefault(a, []).append(b)

        return deps
