"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised settings object — one source of truth for all config."""

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "review_service"
    db_user: str = "root"
    db_password: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # ------------------------------------------------------------------ #
    # Pagination
    # ------------------------------------------------------------------ #
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        """Async MySQL connection URL."""
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()