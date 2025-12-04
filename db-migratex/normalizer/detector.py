# normalizer/detector.py

class AnomalyDetector:
    def detect_repeating_groups(self, columns):
        """
        Very simple heuristic:
        columns like subject1, subject2, subject3 → group "subject"
        """
        groups = {}
        for col in columns:
            prefix = "".join([c for c in col if not c.isdigit()])
            groups.setdefault(prefix, []).append(col)
        return {k: v for k, v in groups.items() if len(v) > 1}

    def detect_duplicate_columns(self, rows):
        """
        Detect columns that always have same value.
        """
        if not rows:
            return []

        cols = rows[0].keys()
        duplicates = []
        for c1 in cols:
            for c2 in cols:
                if c1 >= c2:
                    continue
                same = True
                val = None
                for r in rows:
                    v = r[c1]
                    if val is None:
                        val = v
                    elif v != val:
                        same = False
                        break
                if same:
                    duplicates.append((c1, c2))
        return duplicates
