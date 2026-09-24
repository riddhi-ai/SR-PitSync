"""All settings live here. Values come from the .env file."""
import os
from dotenv import load_dotenv

load_dotenv()


def _list(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


APP_NAME = "SR PITSYNC"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pitsync.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "12"))
CORS_ORIGINS = _list(os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "") or SMTP_USER or "pitsync@localhost"

SEED_PASSWORD = os.getenv("SEED_PASSWORD", "ChangeMe123!")
