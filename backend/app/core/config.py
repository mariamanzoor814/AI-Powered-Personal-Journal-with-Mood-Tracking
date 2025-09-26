# app/core/config.py
from pydantic_settings import BaseSettings
from fastapi_mail import ConnectionConfig
import os

from pydantic_settings import BaseSettings

import logging

logging.basicConfig(
    level=logging.DEBUG,  # 👈 show debug messages
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Personal Journal"

    # Database
    DATABASE_URL: str

    # Auth / JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Email (Mailtrap / SMTP)
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "AI Journal"
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False

    # Hugging Face Inference API
    HF_API_TOKEN: str = None
    HF_SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    HF_EMOTION_MODEL: str = "j-hartmann/emotion-english-distilroberta-base"

     # --- DeepL / Translation settings ---
    # Put your DeepL API key in .env as TRANSLATE_API_KEY
    TRANSLATE_API_KEY: str | None = None
    # Default to the free API endpoint; change to https://api.deepl.com/v2/translate for paid accounts
    TRANSLATE_API_URL: str = "https://api-free.deepl.com/v2/translate"
    TRANSLATE_TIMEOUT: int = 30  # seconds

    class Config:
        env_file = ".env"
        extra = "ignore"  # optional, will skip unknown vars instead of failing

settings = Settings()


# FastAPI-Mail config
mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)
