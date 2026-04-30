-- =========================================
-- DATABASE SETUP
-- =========================================
CREATE DATABASE IF NOT EXISTS abt_dev;
USE abt_dev;

-- =========================================
-- USERS TABLE
-- =========================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Safe insert
INSERT INTO users (name, email)
SELECT 'Test User', 'test@example.com'
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'test@example.com'
);

-- =========================================
-- SUPPORT OPTIONS
-- =========================================
CREATE TABLE IF NOT EXISTS support_options (
    id INT PRIMARY KEY AUTO_INCREMENT,
    type VARCHAR(50) NOT NULL,
    value VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Safe inserts
INSERT INTO support_options (type, value)
SELECT 'email', 'support@company.com'
WHERE NOT EXISTS (
    SELECT 1 FROM support_options WHERE type='email'
);

INSERT INTO support_options (type, value)
SELECT 'phone', '+91 9999999999'
WHERE NOT EXISTS (
    SELECT 1 FROM support_options WHERE type='phone'
);

-- =========================================
-- SUPPORT TICKETS
-- =========================================
CREATE TABLE IF NOT EXISTS support_tickets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NULL,

    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(20),

    message TEXT NOT NULL,

    status VARCHAR(50) DEFAULT 'OPEN',
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- =========================================
-- INDEXES (RUN ONLY FIRST TIME)
-- =========================================
-- ⚠️ Run this section ONLY ONCE, then comment it

CREATE INDEX idx_support_status ON support_tickets(status);
CREATE INDEX idx_support_created ON support_tickets(created_at);

-- =========================================
-- SAMPLE DATA
-- =========================================

INSERT INTO support_tickets (name, email, phone, message)
SELECT 'Aarav Sharma', 'aarav@example.com', '+919876543210', 'Need help with order'
WHERE NOT EXISTS (
    SELECT 1 FROM support_tickets WHERE email='aarav@example.com'
);

INSERT INTO support_tickets (user_id, name, email, phone, message)
SELECT 1, 'Test User', 'test@example.com', '+919999999999', 'Skin concern issue'
WHERE EXISTS (
    SELECT 1 FROM users WHERE id=1
)
AND NOT EXISTS (
    SELECT 1 FROM support_tickets WHERE email='test@example.com'
);

-- =========================================
-- TEST QUERIES
-- =========================================

SELECT * FROM support_tickets;
SELECT * FROM support_tickets WHERE status = 'OPEN';