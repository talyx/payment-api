import asyncio

from app.db.payment_db import init_db as init_payment_db
from app.db.user_db import init_db as init_user_db
from app.utils.logger import logger


async def main():
    await init_user_db()
    logger.info("База данных пользователей инициализирована")
    await init_payment_db()
    logger.info("База данных платежей инициализирована")


if __name__ == "__main__":
    asyncio.run(main())
