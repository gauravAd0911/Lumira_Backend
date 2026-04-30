-- =============================================================================
-- Ecommerce Cart (FastAPI + MySQL)
-- Consolidated SQL: schema + idempotent seed data + reference query templates
-- =============================================================================
-- Notes
-- - Safe to re-run: uses CREATE ... IF NOT EXISTS for schema objects.
-- - Seed section is idempotent (uses WHERE NOT EXISTS checks).
-- - Reference query templates are provided inside a block comment.
-- =============================================================================

-- Recommended session defaults
SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE DATABASE IF NOT EXISTS ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecommerce_db;

-- =============================================================================
-- TABLES
-- =============================================================================

-- Products
CREATE TABLE IF NOT EXISTS products (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  description TEXT NULL,
  price FLOAT NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  image_url TEXT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_products_id (id),
  KEY ix_products_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Carts
CREATE TABLE IF NOT EXISTS carts (
  id INT NOT NULL AUTO_INCREMENT,
  user_id VARCHAR(100) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_carts_id (id),
  KEY ix_carts_user_id (user_id),
  KEY ix_carts_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cart Items
CREATE TABLE IF NOT EXISTS cart_items (
  id INT NOT NULL AUTO_INCREMENT,
  cart_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cart_product (cart_id, product_id),
  KEY ix_cart_items_id (id),
  KEY ix_cart_items_cart_id (cart_id),
  KEY ix_cart_items_product_id (product_id),
  CONSTRAINT fk_cart_items_cart_id FOREIGN KEY (cart_id) REFERENCES carts (id) ON DELETE CASCADE,
  CONSTRAINT fk_cart_items_product_id FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- SEED DATA (idempotent)
-- =============================================================================
-- Comment out this section if you prefer schema-only installs.

START TRANSACTION;

-- setup.sql sample row
INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'Laptop',
  NULL,
  50000,
  10,
  NULL,
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'Laptop'
);

-- seed.sql sample rows
INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'iPhone 15 Pro',
  '6.1-inch Super Retina XDR display, A17 Pro chip',
  999.99,
  50,
  'https://example.com/iphone15.jpg',
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'iPhone 15 Pro'
);

INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'Samsung Galaxy S24',
  '6.2-inch Dynamic AMOLED, Snapdragon 8 Gen 3',
  849.99,
  40,
  'https://example.com/s24.jpg',
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'Samsung Galaxy S24'
);

INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'Sony WH-1000XM5',
  'Industry-leading noise canceling wireless headphones',
  349.99,
  100,
  'https://example.com/wh1000xm5.jpg',
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'Sony WH-1000XM5'
);

INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'MacBook Air M3',
  '13.6-inch Liquid Retina display, 8GB RAM, 256GB SSD',
  1099.00,
  25,
  'https://example.com/macbook-air-m3.jpg',
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'MacBook Air M3'
);

INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'Nike Air Max 270',
  'Lightweight mesh upper with Max Air cushioning',
  150.00,
  200,
  'https://example.com/airmax270.jpg',
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'Nike Air Max 270'
);

INSERT INTO products (name, description, price, stock, image_url, is_active, created_at, updated_at)
SELECT
  'Kindle Paperwhite',
  'Waterproof, 300 ppi glare-free display',
  139.99,
  75,
  'https://example.com/kindle.jpg',
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
WHERE NOT EXISTS (
  SELECT 1 FROM products WHERE name = 'Kindle Paperwhite'
);

COMMIT;

SELECT 'Seed ensured (idempotent).' AS status;

/*
================================================================================
REFERENCE QUERIES (templates)
================================================================================
These mirror the API behavior (implemented via SQLAlchemy ORM) and are provided
for debugging / DBA review / reporting.

Replace :named_params with your driver bindings.

--------------------------------------------------------------------------------
PRODUCTS
--------------------------------------------------------------------------------

-- products_list_active (pagination)
SELECT
  id,
  name,
  description,
  price,
  stock,
  image_url,
  is_active,
  created_at,
  updated_at
FROM products
WHERE is_active = TRUE
ORDER BY id DESC
LIMIT :limit OFFSET :skip;

-- products_get_by_id
SELECT
  id,
  name,
  description,
  price,
  stock,
  image_url,
  is_active,
  created_at,
  updated_at
FROM products
WHERE id = :product_id
LIMIT 1;

-- products_create
INSERT INTO products (
  name,
  description,
  price,
  stock,
  image_url,
  is_active,
  created_at,
  updated_at
)
VALUES (
  :name,
  :description,
  :price,
  :stock,
  :image_url,
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
);

-- products_decrement_stock (when reserving stock; example)
UPDATE products
SET
  stock = stock - :qty,
  updated_at = CURRENT_TIMESTAMP
WHERE id = :product_id
  AND is_active = TRUE
  AND stock >= :qty;

--------------------------------------------------------------------------------
CARTS
--------------------------------------------------------------------------------

-- cart_get_active_for_user
SELECT
  id,
  user_id,
  is_active,
  created_at,
  updated_at
FROM carts
WHERE user_id = :user_id
  AND is_active = TRUE
ORDER BY id DESC
LIMIT 1;

-- cart_create_for_user
INSERT INTO carts (
  user_id,
  is_active,
  created_at,
  updated_at
)
VALUES (
  :user_id,
  TRUE,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
);

-- cart_get_with_items (join)
SELECT
  c.id AS cart_id,
  c.user_id,
  c.is_active,
  c.created_at AS cart_created_at,
  c.updated_at AS cart_updated_at,
  ci.id AS cart_item_id,
  ci.product_id,
  ci.quantity,
  ci.added_at,
  ci.updated_at AS cart_item_updated_at,
  p.name AS product_name,
  p.description AS product_description,
  p.price AS product_price,
  p.stock AS product_stock,
  p.image_url AS product_image_url,
  p.is_active AS product_is_active
FROM carts c
LEFT JOIN cart_items ci ON ci.cart_id = c.id
LEFT JOIN products p ON p.id = ci.product_id
WHERE c.id = :cart_id;

--------------------------------------------------------------------------------
CART ITEMS
--------------------------------------------------------------------------------

-- cart_item_get (for existing item in cart)
SELECT
  id,
  cart_id,
  product_id,
  quantity,
  added_at,
  updated_at
FROM cart_items
WHERE cart_id = :cart_id
  AND product_id = :product_id
LIMIT 1;

-- cart_item_add_or_increment (transactional approach)
START TRANSACTION;

-- Ensure product exists and has stock
SELECT stock
FROM products
WHERE id = :product_id
  AND is_active = TRUE
FOR UPDATE;

-- Ensure active cart exists; create it if missing
SELECT id
FROM carts
WHERE user_id = :user_id
  AND is_active = TRUE
ORDER BY id DESC
LIMIT 1
FOR UPDATE;

-- Insert or increment
INSERT INTO cart_items (
  cart_id,
  product_id,
  quantity,
  added_at,
  updated_at
)
VALUES (
  :cart_id,
  :product_id,
  :delta_qty,
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
)
ON DUPLICATE KEY UPDATE
  quantity = quantity + VALUES(quantity),
  updated_at = UTC_TIMESTAMP();

COMMIT;

-- cart_item_set_quantity
UPDATE cart_items
SET
  quantity = :quantity,
  updated_at = UTC_TIMESTAMP()
WHERE cart_id = :cart_id
  AND product_id = :product_id;

-- cart_item_delete
DELETE FROM cart_items
WHERE cart_id = :cart_id
  AND product_id = :product_id;

-- cart_clear
DELETE FROM cart_items
WHERE cart_id = :cart_id;
*/

