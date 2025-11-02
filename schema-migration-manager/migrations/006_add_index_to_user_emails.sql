-- id: 006
-- description: Add index to users.email for faster lookups

CREATE INDEX idx_users_email ON users(email);

