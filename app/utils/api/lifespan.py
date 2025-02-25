from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.db.payment_db import init_db as init_payment_db
from app.db.user_db import init_db as init_user_db
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """
    Lifespan-контекст для инициализации баз данных.
    """
    #await init_user_db()
    # logger.info("База данных пользователей инициализирована")
    # await init_payment_db()
    # logger.info("База данных платежей инициализирована")
    yield
