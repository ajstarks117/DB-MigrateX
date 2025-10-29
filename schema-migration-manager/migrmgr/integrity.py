"""Simple integrity checks run before and after migrations.

These are extensible heuristics. For now include a basic pre-check that looks
for patterns that would make a NOT NULL constraint fail because of existing
NULL rows.
"""
import re


def _extract_add_column_notnull(sql: str):
    # look for: ALTER TABLE <table> ADD COLUMN <col> <type> NOT NULL
    m = re.search(r"ALTER\s+TABLE\s+(\w+)\s+ADD\s+COLUMN\s+(\w+)[^;]*NOT\s+NULL", sql, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2)
    return None


def run_pre_checks(adapter, migration):
    sql = getattr(migration, 'up_sql', '') or ''
    found = _extract_add_column_notnull(sql)
    if found:
        table, col = found
        # If the column already exists, check for NULLs that would violate NOT NULL
        try:
            q = f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL;"
            row = adapter.fetchone(q)
            count = row[0] if row is not None else 0
            if count > 0:
                raise Exception(
                    f"Integrity check failed: {count} NULL rows would violate NOT NULL for {col} on {table}"
                )
        except Exception as exc:
            # if the column doesn't exist yet, some adapters may error; allow migration to proceed
            # caller can use --skip-integrity to bypass checks; treat adapter errors as failures
            if isinstance(exc, Exception) and 'no such column' in str(exc).lower():
                # Column doesn't exist yet; it's safer to continue (real enforcement happens after apply)
                return
            raise


def run_post_checks(adapter, migration):
    
    return
