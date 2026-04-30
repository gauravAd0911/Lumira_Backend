from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ShopFlow"
    app_env:  str = "development"
    secret_key: str = "change-me"

    # Database
    database_url: str = "mysql+pymysql://ecommerce_user:Root@localhost:3306/abt_dev?charset=utf8mb4"

    # OTP
    otp_expire_minutes:      int  = 10
    otp_max_attempts:        int  = 5
    otp_max_resends:         int  = 3
    otp_resend_cooldown_secs: int = 60
    dev_show_code:           bool = False

    # Twilio SMS
    sms_enabled:        bool = False
    twilio_account_sid: str  = ""
    twilio_auth_token:  str  = ""
    twilio_sms_from:    str  = ""

    # CORS
    allowed_origins: str = "http://localhost:8000"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
