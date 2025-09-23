CREATE TABLE IF NOT EXISTS schema_versions (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    rollback_sql TEXT
);