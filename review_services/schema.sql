-- =============================================================================
-- Review Service — Full Database Schema
-- Engine : MySQL 8.0+
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: products
-- Stores the product catalogue referenced by reviews.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id   CHAR(36)     NOT NULL DEFAULT (UUID()),
    name         VARCHAR(255) NOT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_products PRIMARY KEY (product_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Product catalogue';

-- -----------------------------------------------------------------------------
-- Table: users
-- Minimal user record; full user data lives in the User Service.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id      CHAR(36)     NOT NULL DEFAULT (UUID()),
    email        VARCHAR(320) NOT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_users           PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email     UNIQUE       (email)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Shadow user table for FK integrity';

-- -----------------------------------------------------------------------------
-- Table: orders
-- Used exclusively for verified-purchaser eligibility checks.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id     CHAR(36)     NOT NULL DEFAULT (UUID()),
    user_id      CHAR(36)     NOT NULL,
    product_id   CHAR(36)     NOT NULL,
    status       VARCHAR(50)  NOT NULL COMMENT 'e.g. COMPLETED, CANCELLED',
    purchased_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_orders           PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_user      FOREIGN KEY (user_id)    REFERENCES users    (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_orders_product   FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE,

    INDEX idx_orders_user_product (user_id, product_id),
    INDEX idx_orders_status       (status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Purchase records for eligibility gating';

-- -----------------------------------------------------------------------------
-- Table: reviews
-- Core review entity.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    review_id    CHAR(36)       NOT NULL DEFAULT (UUID()),
    product_id   CHAR(36)       NOT NULL,
    user_id      CHAR(36)       NOT NULL,
    rating       TINYINT        NOT NULL COMMENT '1–5 inclusive',
    title        VARCHAR(255)   NOT NULL,
    body         TEXT           NOT NULL,
    is_verified  TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '1 = verified purchaser',
    status       VARCHAR(30)    NOT NULL DEFAULT 'PUBLISHED'
                                COMMENT 'PUBLISHED | HIDDEN | DELETED',
    created_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_reviews             PRIMARY KEY (review_id),
    CONSTRAINT fk_reviews_product     FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_user        FOREIGN KEY (user_id)    REFERENCES users    (user_id)    ON DELETE CASCADE,
    CONSTRAINT chk_reviews_rating     CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT chk_reviews_status     CHECK (status IN ('PUBLISHED', 'HIDDEN', 'DELETED')),
    -- One review per user per product
    CONSTRAINT uq_reviews_user_product UNIQUE (user_id, product_id),

    INDEX idx_reviews_product_created (product_id, created_at DESC),
    INDEX idx_reviews_user            (user_id),
    INDEX idx_reviews_status          (status),
    INDEX idx_reviews_rating          (rating)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='User-submitted product reviews';

-- =============================================================================
-- Views
-- =============================================================================

-- Aggregated rating summary per product (used by /rating-summary endpoint)
CREATE OR REPLACE VIEW vw_product_rating_summary AS
SELECT
    r.product_id,
    COUNT(*)                                     AS total_reviews,
    ROUND(AVG(r.rating), 2)                      AS average_rating,
    SUM(r.rating = 5)                            AS five_star,
    SUM(r.rating = 4)                            AS four_star,
    SUM(r.rating = 3)                            AS three_star,
    SUM(r.rating = 2)                            AS two_star,
    SUM(r.rating = 1)                            AS one_star,
    SUM(r.is_verified = 1)                       AS verified_count
FROM reviews r
WHERE r.status = 'PUBLISHED'
GROUP BY r.product_id;

-- =============================================================================
-- Stored Procedures
-- =============================================================================

DELIMITER $$

-- Eligibility check: returns 1 if the user has a COMPLETED order for the product
CREATE PROCEDURE IF NOT EXISTS sp_is_verified_purchaser(
    IN  p_user_id    CHAR(36),
    IN  p_product_id CHAR(36),
    OUT p_eligible   TINYINT
)
BEGIN
    SELECT COUNT(*) > 0
    INTO   p_eligible
    FROM   orders
    WHERE  user_id    = p_user_id
      AND  product_id = p_product_id
      AND  status     = 'COMPLETED'
    LIMIT  1;
END$$

DELIMITER ;

-- =============================================================================
-- Queries — used directly by the repository layer
-- =============================================================================

-- Q1: Paginated review list for a product (PUBLISHED only, newest first)
-- :product_id  CHAR(36)
-- :limit       INT
-- :offset      INT
-- SELECT
--     r.review_id,
--     r.user_id,
--     r.rating,
--     r.title,
--     r.body,
--     r.is_verified,
--     r.created_at,
--     r.updated_at
-- FROM   reviews r
-- WHERE  r.product_id = :product_id
--   AND  r.status     = 'PUBLISHED'
-- ORDER  BY r.created_at DESC
-- LIMIT  :limit
-- OFFSET :offset;

-- Q2: Total count for pagination header
-- SELECT COUNT(*) AS total
-- FROM   reviews
-- WHERE  product_id = :product_id
--   AND  status     = 'PUBLISHED';

-- Q3: Rating summary (via view)
-- SELECT * FROM vw_product_rating_summary WHERE product_id = :product_id;

-- Q4: Fetch single review by PK
-- SELECT * FROM reviews WHERE review_id = :review_id;

-- Q5: Fetch all reviews authored by a specific user (newest first)
-- SELECT * FROM reviews WHERE user_id = :user_id ORDER BY created_at DESC;

-- Q6: Insert new review
-- INSERT INTO reviews (review_id, product_id, user_id, rating, title, body, is_verified)
-- VALUES (:review_id, :product_id, :user_id, :rating, :title, :body, :is_verified);

-- Q7: Patch existing review (only mutable fields)
-- UPDATE reviews
-- SET    rating     = COALESCE(:rating, rating),
--        title      = COALESCE(:title,  title),
--        body       = COALESCE(:body,   body),
--        updated_at = CURRENT_TIMESTAMP
-- WHERE  review_id  = :review_id
--   AND  user_id    = :user_id;

-- =============================================================================
-- Transactional Outbox
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: outbox_events
-- Written atomically with every review mutation.
-- Polled by the OutboxRelayWorker; rows are never deleted — status tracks lifecycle.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outbox_events (
    event_id        CHAR(36)      NOT NULL DEFAULT (UUID()),
    event_type      VARCHAR(100)  NOT NULL COMMENT 'e.g. review.created, review.updated',
    aggregate_id    CHAR(36)      NOT NULL COMMENT 'review_id of the affected review',
    payload         JSON          NOT NULL COMMENT 'Full event payload',
    status          VARCHAR(20)   NOT NULL DEFAULT 'PENDING'
                                  COMMENT 'PENDING | DISPATCHED | FAILED',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dispatched_at   DATETIME      NULL,

    CONSTRAINT pk_outbox_events       PRIMARY KEY (event_id),
    CONSTRAINT chk_outbox_status      CHECK (status IN ('PENDING', 'DISPATCHED', 'FAILED')),

    -- Relay worker queries by status + created_at (oldest PENDING first)
    INDEX idx_outbox_status_created   (status, created_at ASC)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Transactional outbox — relay worker forwards rows to the message broker';

-- Q-OUTBOX-1: Relay fetch — SELECT ... FOR UPDATE SKIP LOCKED
-- SELECT event_id, event_type, aggregate_id, payload
-- FROM   outbox_events
-- WHERE  status = 'PENDING'
-- ORDER  BY created_at ASC
-- LIMIT  :batch_size
-- FOR UPDATE SKIP LOCKED;

-- Q-OUTBOX-2: Mark dispatched
-- UPDATE outbox_events
-- SET    status = 'DISPATCHED', dispatched_at = NOW()
-- WHERE  event_id = :event_id;

-- Q-OUTBOX-3: Mark failed
-- UPDATE outbox_events
-- SET    status = 'FAILED'
-- WHERE  event_id = :event_id;