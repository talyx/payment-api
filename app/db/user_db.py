import asyncio
import random
from decimal import Decimal

from sqlalchemy import DECIMAL, Integer, create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.config import USER_DATABASE_URL, USER_DATABASE_URL_SYNC, USER_DB
from app.exception.custom_exception import NotEnoughMoney, UserNotFoundError
from app.utils.logger import logger

engine = create_async_engine(
    USER_DATABASE_URL, echo=False, pool_size=15, max_overflow=0
)
engine_sync = create_engine(USER_DATABASE_URL_SYNC)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)


async def init_db():
    if not database_exists(engine_sync.url):
        logger.info(f"База данных {USER_DB} не найдена. Создаём базу...")
        create_database(engine_sync.url)
        logger.info(f"База данных {USER_DB} успешно создана.")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        if not users:
            for _ in range(5):
                new_user = User(balance=round(random.uniform(500, 1000), 2))
                session.add(new_user)
            await session.commit()


async def simulate_db_delay():
    rnd = random.random()
    if rnd < 0.1:
        await asyncio.sleep(60)
    elif rnd < 0.2:
        await asyncio.sleep(2)
    else:
        await asyncio.sleep(random.uniform(0.1, 0.3))


async def get_user(user_id: int, session: AsyncSession):
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(f"User with id {user_id} not found")
    return user


async def update_user_balance(
    user_id: int, amount: Decimal, session: AsyncSession
) -> bool:
    user = await get_user(user_id, session)
    new_balance = user.balance - amount
    if new_balance < 0:
        raise NotEnoughMoney(f"User with id {user_id} has not enough money")
    user.balance = new_balance
    session.add(user)
    await session.flush()
    return True


async def check_user_data(user_id: int, amount: Decimal) -> bool:
    async with async_session() as session:
        user = await get_user(user_id, session)
        if user.balance < amount:
            raise NotEnoughMoney(f"User with id {user_id} has not enough money")
        return True
