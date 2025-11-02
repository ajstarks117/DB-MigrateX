CREATE TABLE schema_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version VARCHAR(50) UNIQUE,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
