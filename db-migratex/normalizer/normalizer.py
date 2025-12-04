# normalizer/normalizer.py
from .detector import AnomalyDetector
from .dependencies import FunctionalDependencyDetector


class SchemaNormalizer:
    """
    For demo:
    - assumes rows from raw_students with fields: id, legacy_id, name, age, department
    - detects FD: legacy_id -> name, age, department
    - Suggests students_norm(id, name, age, department) with legacy_id as PK
    """

    def analyze(self, rows):
        if not rows:
            return {"columns": [], "fds": {}, "repeating_groups": {}, "duplicates": []}

        detector = AnomalyDetector()
        fdd = FunctionalDependencyDetector()

        columns = list(rows[0].keys())
        repeating = detector.detect_repeating_groups(columns)
        duplicates = detector.detect_duplicate_columns(rows)
        fds = fdd.find_dependencies(rows)

        return {
            "columns": columns,
            "repeating_groups": repeating,
            "duplicates": duplicates,
            "functional_dependencies": fds,
        }
