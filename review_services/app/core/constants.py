"""Domain-level constants for the Review Service."""

# ------------------------------------------------------------------ #
# Review status values
# ------------------------------------------------------------------ #
REVIEW_STATUS_PUBLISHED: str = "PUBLISHED"
REVIEW_STATUS_HIDDEN: str = "HIDDEN"
REVIEW_STATUS_DELETED: str = "DELETED"

ALLOWED_REVIEW_STATUSES: frozenset[str] = frozenset(
    {REVIEW_STATUS_PUBLISHED, REVIEW_STATUS_HIDDEN, REVIEW_STATUS_DELETED}
)

# ------------------------------------------------------------------ #
# Rating bounds
# ------------------------------------------------------------------ #
RATING_MIN: int = 1
RATING_MAX: int = 5

# ------------------------------------------------------------------ #
# Order status that qualifies a purchaser as verified
# ------------------------------------------------------------------ #
ORDER_STATUS_COMPLETED: str = "COMPLETED"

# ------------------------------------------------------------------ #
# Error messages
# ------------------------------------------------------------------ #
ERR_REVIEW_NOT_FOUND: str = "Review not found."
ERR_PRODUCT_NOT_FOUND: str = "Product not found."
ERR_REVIEW_ALREADY_EXISTS: str = "You have already reviewed this product."
ERR_NOT_VERIFIED_PURCHASER: str = (
    "Only verified purchasers may submit a review for this product."
)
ERR_REVIEW_NOT_OWNED: str = "You do not own this review."

# ------------------------------------------------------------------ #
# Outbox / domain event types
# ------------------------------------------------------------------ #
EVENT_REVIEW_CREATED: str = "review.created"
EVENT_REVIEW_UPDATED: str = "review.updated"

# Outbox relay poll interval in seconds
OUTBOX_POLL_INTERVAL_SECONDS: int = 5

# Maximum events fetched per relay cycle
OUTBOX_BATCH_SIZE: int = 100

# Outbox event statuses
OUTBOX_STATUS_PENDING: str = "PENDING"
OUTBOX_STATUS_DISPATCHED: str = "DISPATCHED"
OUTBOX_STATUS_FAILED: str = "FAILED"