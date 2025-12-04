-- id: 001
-- description: create raw staging table for legacy BoxPro data
-- down_filename: 001_create_raw_students.down.sql

CREATE TABLE IF NOT EXISTS raw_students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    legacy_id VARCHAR(20),
    name VARCHAR(100),
    age INT,
    department VARCHAR(50)
);
