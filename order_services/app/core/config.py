import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "abt_order_db")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "Gaurav@123")
    DB_URL = os.getenv("DB_URL") or f"mysql+pymysql://{DB_USER}:{quote(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    TWILIO_SID = os.getenv("TWILIO_SID") or os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH = os.getenv("TWILIO_AUTH") or os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE") or os.getenv("TWILIO_PHONE_NUMBER") or os.getenv("TWILIO_FROM_NUMBER")

    SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or 587)
    SMTP_USER = os.getenv("SMTP_USER", "").strip()
    SMTP_PASS = (os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD") or "").strip()
    SMTP_FROM_EMAIL = (os.getenv("SMTP_FROM_EMAIL") or os.getenv("EMAIL_FROM") or "").strip() or SMTP_USER
    SMTP_USE_TLS = _env_bool("SMTP_USE_TLS", "true")
    ENABLE_ORDER_NOTIFICATIONS = _env_bool("ENABLE_ORDER_NOTIFICATIONS", "true")

    # MVP: Stock Management
    ENABLE_STOCK_RESERVATION = _env_bool("ENABLE_STOCK_RESERVATION")
    DEDUCT_STOCK_ON_ORDER = _env_bool("DEDUCT_STOCK_ON_ORDER")


settings = Settings()

