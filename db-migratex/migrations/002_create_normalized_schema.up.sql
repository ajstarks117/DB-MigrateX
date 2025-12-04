-- id: 002
-- description: create normalized students schema
-- down_filename: 002_create_normalized_schema.down.sql

CREATE TABLE IF NOT EXISTS students_norm (
    id INT PRIMARY KEY AUTO_INCREMENT,
    legacy_id VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    age INT,
    department VARCHAR(50)
);
