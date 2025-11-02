-- id: 007
-- description: Add phone column and length constraints on users

ALTER TABLE users
ADD COLUMN phone VARCHAR(15);

ALTER TABLE users
MODIFY COLUMN name VARCHAR(80) NOT NULL;
