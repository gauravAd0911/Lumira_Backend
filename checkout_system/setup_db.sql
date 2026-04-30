-- ============================================================
--  ShopFlow — MySQL Setup
--  Run: mysql -u root -p < setup_db.sql
-- ============================================================

DROP DATABASE IF EXISTS abt_dev;
CREATE DATABASE abt_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

DROP USER IF EXISTS 'ecommerce_user'@'localhost';
CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY 'Root';
GRANT ALL PRIVILEGES ON abt_dev.* TO 'ecommerce_user'@'localhost';
FLUSH PRIVILEGES;

USE abt_dev;

-- ── categories ────────────────────────────────────────────────
CREATE TABLE categories (
    id          CHAR(36)    NOT NULL DEFAULT (UUID()),
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(120) NOT NULL,
    description TEXT,
    is_active   TINYINT(1)  NOT NULL DEFAULT 1,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_cat_name (name),
    UNIQUE KEY uq_cat_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── products ──────────────────────────────────────────────────
CREATE TABLE products (
    id            CHAR(36)      NOT NULL DEFAULT (UUID()),
    category_id   CHAR(36),
    name          VARCHAR(255)  NOT NULL,
    slug          VARCHAR(280)  NOT NULL,
    description   TEXT,
    price         DECIMAL(12,2) NOT NULL,
    compare_price DECIMAL(12,2),
    sku           VARCHAR(100),
    stock_qty     INT           NOT NULL DEFAULT 0,
    images        JSON,
    is_active     TINYINT(1)   NOT NULL DEFAULT 1,
    created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_prod_slug (slug),
    UNIQUE KEY uq_prod_sku  (sku),
    KEY idx_prod_cat       (category_id),
    KEY idx_prod_active    (is_active),
    CONSTRAINT fk_prod_cat FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── guest_checkout_sessions ───────────────────────────────────
CREATE TABLE guest_checkout_sessions (
    id                 CHAR(36)     NOT NULL DEFAULT (UUID()),
    guest_name         VARCHAR(200),
    email              VARCHAR(320) NOT NULL,
    phone              VARCHAR(30)  NOT NULL,
    purpose            VARCHAR(30)  NOT NULL DEFAULT 'checkout',
    email_verified     TINYINT(1)   NOT NULL DEFAULT 0,
    sms_verified  TINYINT(1)   NOT NULL DEFAULT 0,
    session_token      VARCHAR(512),
    session_expires_at DATETIME(6),
    ip_address         VARCHAR(45),
    created_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_session_token (session_token(255)),
    KEY idx_session_email   (email),
    KEY idx_session_purpose (purpose)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── guest_otps ────────────────────────────────────────────────
CREATE TABLE guest_otps (
    id             CHAR(36)     NOT NULL DEFAULT (UUID()),
    session_id     CHAR(36)     NOT NULL,
    channel        ENUM('email','sms')                           NOT NULL,
    purpose        ENUM('checkout','order_lookup')                NOT NULL,
    code_hash      CHAR(64)     NOT NULL,
    status         ENUM('pending','verified','expired','locked')  NOT NULL DEFAULT 'pending',
    attempts       SMALLINT     NOT NULL DEFAULT 0,
    resend_count   SMALLINT     NOT NULL DEFAULT 0,
    expires_at     DATETIME(6)  NOT NULL,
    verified_at    DATETIME(6),
    last_resent_at DATETIME(6),
    plain_code     VARCHAR(10)  COMMENT 'Dev only — set NULL in production',
    created_at     DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_otp_session (session_id),
    KEY idx_otp_status  (status),
    KEY idx_otp_expires (expires_at),
    CONSTRAINT fk_otp_session FOREIGN KEY (session_id)
        REFERENCES guest_checkout_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── addresses ─────────────────────────────────────────────────
CREATE TABLE addresses (
    id          CHAR(36)     NOT NULL DEFAULT (UUID()),
    full_name   VARCHAR(200) NOT NULL,
    line1       VARCHAR(255) NOT NULL,
    line2       VARCHAR(255),
    city        VARCHAR(100) NOT NULL,
    state       VARCHAR(100),
    postal_code VARCHAR(20)  NOT NULL,
    country     CHAR(2)      NOT NULL DEFAULT 'US',
    phone       VARCHAR(30),
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── guest_orders ──────────────────────────────────────────────
CREATE TABLE guest_orders (
    id                  CHAR(36)      NOT NULL DEFAULT (UUID()),
    session_id          CHAR(36),
    order_number        VARCHAR(20)   NOT NULL,
    guest_name          VARCHAR(200)  NOT NULL,
    guest_email         VARCHAR(320)  NOT NULL,
    guest_phone         VARCHAR(30),
    email_verified      TINYINT(1)    NOT NULL DEFAULT 0,
    sms_verified   TINYINT(1)    NOT NULL DEFAULT 0,
    shipping_address_id CHAR(36),
    billing_address_id  CHAR(36),
    items               JSON          NOT NULL,
    subtotal            DECIMAL(12,2) NOT NULL,
    shipping_amount     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_amount          DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    discount_amount     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_amount        DECIMAL(12,2) NOT NULL,
    currency            CHAR(3)       NOT NULL DEFAULT 'USD',
    status              VARCHAR(30)   NOT NULL DEFAULT 'pending',
    payment_status      VARCHAR(30)   NOT NULL DEFAULT 'unpaid',
    payment_method      VARCHAR(50),
    notes               TEXT,
    ip_address          VARCHAR(45),
    created_at          DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at          DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_order_number   (order_number),
    KEY idx_order_email          (guest_email),
    KEY idx_order_status         (status),
    KEY idx_order_created        (created_at),
    CONSTRAINT fk_order_session  FOREIGN KEY (session_id) REFERENCES guest_checkout_sessions(id) ON DELETE SET NULL,
    CONSTRAINT fk_order_shipping FOREIGN KEY (shipping_address_id) REFERENCES addresses(id) ON DELETE SET NULL,
    CONSTRAINT fk_order_billing  FOREIGN KEY (billing_address_id)  REFERENCES addresses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── order_status_history ──────────────────────────────────────
CREATE TABLE order_status_history (
    id         CHAR(36)    NOT NULL DEFAULT (UUID()),
    order_id   CHAR(36)    NOT NULL,
    old_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    note       TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_history_order (order_id),
    CONSTRAINT fk_history_order FOREIGN KEY (order_id) REFERENCES guest_orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Seed data ─────────────────────────────────────────────────
INSERT INTO categories (id, name, slug, description) VALUES
    (UUID(), 'Electronics',   'electronics',  'Gadgets and devices'),
    (UUID(), 'Clothing',      'clothing',     'Fashion for all seasons'),
    (UUID(), 'Home & Garden', 'home-garden',  'For your living space'),
    (UUID(), 'Sports',        'sports',       'Gear for every athlete'),
    (UUID(), 'Books',         'books',        'Knowledge at your fingertips');

INSERT INTO products (id, category_id, name, slug, description, price, compare_price, sku, stock_qty, images)
SELECT UUID(), id, 'Wireless Headphones Pro', 'wireless-headphones-pro',
    'Noise-cancelling, 30hr battery.', 149.99, 199.99, 'ELEC-001', 50,
    '[{"url":"/static/headphones.jpg"}]'
FROM categories WHERE slug='electronics' LIMIT 1;

INSERT INTO products (id, category_id, name, slug, description, price, compare_price, sku, stock_qty, images)
SELECT UUID(), id, 'Premium Cotton T-Shirt', 'premium-cotton-tshirt',
    '100% organic cotton, 12 colours.', 29.99, 39.99, 'CLO-001', 200,
    '[{"url":"/static/tshirt.jpg"}]'
FROM categories WHERE slug='clothing' LIMIT 1;

INSERT INTO products (id, category_id, name, slug, description, price, compare_price, sku, stock_qty, images)
SELECT UUID(), id, 'Ergonomic Office Chair', 'ergonomic-office-chair',
    'Lumbar support, breathable mesh.', 349.00, NULL, 'HG-001', 15,
    '[{"url":"/static/chair.jpg"}]'
FROM categories WHERE slug='home-garden' LIMIT 1;

INSERT INTO products (id, category_id, name, slug, description, price, compare_price, sku, stock_qty, images)
SELECT UUID(), id, 'Smart Watch Series X', 'smart-watch-series-x',
    'GPS, health tracking, 7-day battery.', 299.00, 399.00, 'ELEC-002', 30,
    '[{"url":"/static/watch.jpg"}]'
FROM categories WHERE slug='electronics' LIMIT 1;

INSERT INTO products (id, category_id, name, slug, description, price, compare_price, sku, stock_qty, images)
SELECT UUID(), id, 'Yoga Mat Premium', 'yoga-mat-premium',
    'Non-slip, 6mm, eco-friendly.', 49.99, 69.99, 'SPT-001', 80,
    '[{"url":"/static/yoga.jpg"}]'
FROM categories WHERE slug='sports' LIMIT 1;

SELECT 'ShopFlow DB ready!' AS status;