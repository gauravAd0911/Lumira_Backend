from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Ecommerce Cart API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ecommerce_db"
    DB_USER: str = "root"
    DB_PASSWORD: str = "Root"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
