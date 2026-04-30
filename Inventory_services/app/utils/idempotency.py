from typing import Optional


def normalize_idempotency_key(key: Optional[str]) -> Optional[str]:
    """
    Normalize idempotency key to avoid duplicates caused by formatting issues.

    :param key: Raw idempotency key
    :return: Cleaned key or None
    """
    if key is None:
        return None

    normalized = key.strip()
    return normalized if normalized else None