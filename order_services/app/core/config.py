import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_URL = os.getenv("DB_URL")

    TWILIO_SID = os.getenv("TWILIO_SID") or os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH = os.getenv("TWILIO_AUTH") or os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE") or os.getenv("TWILIO_PHONE_NUMBER")


settings = Settings()
