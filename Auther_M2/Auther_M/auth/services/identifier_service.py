from __future__ import annotations

import os
import re


_PHONE_CLEAN_RE = re.compile(r"[^0-9+]" )


def normalize_email(email: str) -> str:
    """Normalize email for lookups."""

    return email.strip().lower()


def normalize_phone(phone: str) -> str:
    """Normalize phone to a compact E.164-ish representation.

    Keeps leading + and digits, strips spaces/hyphens.
    """

    raw = phone.strip()
    cleaned = _PHONE_CLEAN_RE.sub("", raw)
    return cleaned


def is_email_identifier(identifier: str) -> bool:
    """Return True if identifier looks like an email."""

    return "@" in identifier


def normalize_identifier(identifier: str) -> tuple[str, str]:
    """Return (kind, normalized_value) where kind is 'email' or 'phone'."""

    ident = identifier.strip()
    if is_email_identifier(ident):
        return "email", normalize_email(ident)

    return "phone", normalize_phone(ident)
