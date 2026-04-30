from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    DATABASE_URL: str

    # ✅ allow extra fields from .env
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )


settings = Settings()