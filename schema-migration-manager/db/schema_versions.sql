CREATE TABLE IF NOT EXISTS schema_versions (
    migration_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_by TEXT,
    applied_at TEXT DEFAULT (datetime('now')),
    down_filename TEXT,
    notes TEXT
);
