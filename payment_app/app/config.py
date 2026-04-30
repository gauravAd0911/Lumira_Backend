"""Application configuration loaded from `.env`."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _clean_env_value(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


RAZORPAY_KEY = _clean_env_value(os.getenv("RAZORPAY_KEY", ""))
RAZORPAY_SECRET = _clean_env_value(os.getenv("RAZORPAY_SECRET", ""))
RAZORPAY_WEBHOOK_SECRET = _clean_env_value(os.getenv("RAZORPAY_WEBHOOK_SECRET", ""))
