import os
from urllib.parse import urlunparse

from dotenv import load_dotenv

load_dotenv()


def build_db_url(db_name):
    return urlunparse(
        (
            "postgresql+asyncpg",
            f"{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}",
            f"/{db_name}",
            "",
            "",
            "",
        )
    )


DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
PAYMENT_DB = os.getenv("DATABASE_PAYMENT_NAME", "payment_db")
USER_DB = os.getenv("DATABASE_USER_NAME", "user_db")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", default="testpass")
DATABASE_USER = os.getenv("DATABASE_USER", "testuser")

PAYMENT_DATABASE_URL = build_db_url(PAYMENT_DB)
PAYMENT_DATABASE_URL_SYNC = PAYMENT_DATABASE_URL.replace("+asyncpg", "")

USER_DATABASE_URL = build_db_url(USER_DB)
USER_DATABASE_URL_SYNC = USER_DATABASE_URL.replace("+asyncpg", "")


LOYALTY_HOST = os.getenv("LOYALTY_HOST", "localhost")
LOYALTY_PORT = int(os.getenv("LOYALTY_PORT", "8001"))
NOTIFICATION_HOST = os.getenv("NOTIFICATION_HOST", "localhost")
NOTIFICATION_PORT = int(os.getenv("NOTIFICATION_PORT", "8002"))

LOYALTY_SERVICE_URL = f"http://{LOYALTY_HOST}:{LOYALTY_PORT}/loyalty"
NOTIFICATION_SERVICE_URL = f"http://{NOTIFICATION_HOST}:{NOTIFICATION_PORT}/notify"
