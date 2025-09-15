CREATE TABLE IF NOT EXISTS schema_versions (
    version Varchar(50) Primary Key,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
