import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application configuration settings."""

    def __init__(self):
        # =========================
        # DATABASE
        # =========================
        self.DATABASE_URL: str = os.getenv("DATABASE_URL")

        # =========================
        # SECURITY
        # =========================
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret")
        self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
        )

        # =========================
        # APP SETTINGS
        # =========================
        self.DEBUG: bool = os.getenv("DEBUG", "True") == "True"
        self.APP_NAME: str = os.getenv("APP_NAME", "User Profile Service")

        # =========================
        # BUSINESS LOGIC
        # =========================
        self.MAX_ADDRESS_LIMIT: int = int(
            os.getenv("MAX_ADDRESS_LIMIT", 5)
        )


# Singleton instance
settings = Settings()