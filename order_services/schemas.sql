CREATE DATABASE abt_dev;
USE abt_dev;

-- Orders Table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE,
    user_id VARCHAR(100) NOT NULL,
    guest_token VARCHAR(255),
    total DECIMAL(10,2),
    status VARCHAR(50),
    payment_method VARCHAR(50),
    shipping_address TEXT,
    item_count INT,
    primary_label VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Items Snapshot
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    product_name VARCHAR(255),
    price DECIMAL(10,2),
    quantity INT,
    image_url TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Tracking Timeline
CREATE TABLE order_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    status VARCHAR(50),
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);