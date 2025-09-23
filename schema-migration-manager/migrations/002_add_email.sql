-- Add email column allowing NULL initially
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;

-- Add index for better performance on email queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

