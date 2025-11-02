-- id: 004
-- description: Add status column with default value

ALTER TABLE orders
ADD COLUMN status VARCHAR(20) DEFAULT 'PENDING';
