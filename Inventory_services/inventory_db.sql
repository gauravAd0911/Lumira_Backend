-- ============================================================
-- INVENTORY SERVICE - CLEAN VERSION
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- WAREHOUSE TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- PRODUCTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- ============================================================
-- STOCK TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS stock (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,

    total_quantity INT NOT NULL DEFAULT 0,
    reserved_quantity INT NOT NULL DEFAULT 0,

    -- safer computed column
    available_quantity INT GENERATED ALWAYS AS (total_quantity - reserved_quantity) STORED,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_stock_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_stock_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,

    UNIQUE KEY uniq_product_warehouse (product_id, warehouse_id),
    INDEX idx_stock_product (product_id)
) ENGINE=InnoDB;

-- ============================================================
-- RESERVATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS reservations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    quantity INT NOT NULL,

    status ENUM('ACTIVE','COMMITTED','RELEASED','EXPIRED') NOT NULL DEFAULT 'ACTIVE',

    idempotency_key VARCHAR(64) UNIQUE,

    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_res_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT fk_res_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,

    INDEX idx_res_status_expiry (status, expires_at),
    INDEX idx_res_product (product_id)
) ENGINE=InnoDB;

-- ============================================================
-- STOCK LEDGER
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_ledger (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,

    change_type ENUM('RESERVE','RELEASE','COMMIT','ADJUST') NOT NULL,
    quantity INT NOT NULL,

    reference_id BIGINT NULL,
    reference_type VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ledger_product (product_id),
    INDEX idx_ledger_ref (reference_id)
) ENGINE=InnoDB;

-- ============================================================
-- TRIGGER: RESERVE
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_reservation_insert
AFTER INSERT ON reservations
FOR EACH ROW
BEGIN
    IF NEW.status = 'ACTIVE' THEN
        UPDATE stock
        SET reserved_quantity = reserved_quantity + NEW.quantity
        WHERE product_id = NEW.product_id
          AND warehouse_id = NEW.warehouse_id;

        INSERT INTO stock_ledger(product_id, warehouse_id, change_type, quantity, reference_id, reference_type)
        VALUES (NEW.product_id, NEW.warehouse_id, 'RESERVE', NEW.quantity, NEW.id, 'RESERVATION');
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- TRIGGER: UPDATE (RELEASE + COMMIT)
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_reservation_update
AFTER UPDATE ON reservations
FOR EACH ROW
BEGIN
    -- RELEASE / EXPIRE
    IF OLD.status = 'ACTIVE' AND NEW.status IN ('RELEASED','EXPIRED') THEN
        UPDATE stock
        SET reserved_quantity = GREATEST(reserved_quantity - OLD.quantity, 0)
        WHERE product_id = OLD.product_id
          AND warehouse_id = OLD.warehouse_id;

        INSERT INTO stock_ledger(product_id, warehouse_id, change_type, quantity, reference_id, reference_type)
        VALUES (OLD.product_id, OLD.warehouse_id, 'RELEASE', OLD.quantity, OLD.id, 'RESERVATION');
    END IF;

    -- COMMIT
    IF OLD.status = 'ACTIVE' AND NEW.status = 'COMMITTED' THEN
        UPDATE stock
        SET 
            reserved_quantity = GREATEST(reserved_quantity - OLD.quantity, 0),
            total_quantity = GREATEST(total_quantity - OLD.quantity, 0)
        WHERE product_id = OLD.product_id
          AND warehouse_id = OLD.warehouse_id;

        INSERT INTO stock_ledger(product_id, warehouse_id, change_type, quantity, reference_id, reference_type)
        VALUES (OLD.product_id, OLD.warehouse_id, 'COMMIT', OLD.quantity, OLD.id, 'RESERVATION');
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- CLEANUP QUERY
-- ============================================================
UPDATE reservations
SET status = 'EXPIRED'
WHERE status = 'ACTIVE'
  AND expires_at < NOW();

-- ============================================================
-- SAFETY CHECK
-- ============================================================
ALTER TABLE stock
ADD CONSTRAINT chk_positive_stock
CHECK (total_quantity >= 0 AND reserved_quantity >= 0);

SET FOREIGN_KEY_CHECKS = 1;