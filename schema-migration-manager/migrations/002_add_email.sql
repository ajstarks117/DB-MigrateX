-- id: 002
-- description: Add email column to users table

ALTER TABLE users
ADD COLUMN email VARCHAR(150) UNIQUE;
