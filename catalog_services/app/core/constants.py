"""Domain-level constants shared across the Catalog Service."""

# ── Pagination ──────────────────────────────────────────────────────────────
MIN_PAGE: int = 1
MIN_LIMIT: int = 1

# ── Sort options ────────────────────────────────────────────────────────────
SORT_PRICE_ASC: str = "price_asc"
SORT_PRICE_DESC: str = "price_desc"
SORT_RATING_DESC: str = "rating_desc"
SORT_NEWEST: str = "newest"
SORT_POPULAR: str = "popular"

ALLOWED_SORT_VALUES: frozenset[str] = frozenset(
    {SORT_PRICE_ASC, SORT_PRICE_DESC, SORT_RATING_DESC, SORT_NEWEST, SORT_POPULAR}
)

# ── Home page ───────────────────────────────────────────────────────────────
FEATURED_PRODUCTS_LIMIT: int = 10
HOME_BANNER_LIMIT: int = 5

# ── Product ─────────────────────────────────────────────────────────────────
AVAILABILITY_IN_STOCK: str = "in_stock"
AVAILABILITY_OUT_OF_STOCK: str = "out_of_stock"
AVAILABILITY_LOW_STOCK: str = "low_stock"