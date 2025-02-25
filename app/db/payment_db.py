import asyncio
import random
from decimal import Decimal

from sqlalchemy import DECIMAL, Integer, String, create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from app.config import (PAYMENT_DATABASE_URL, PAYMENT_DATABASE_URL_SYNC,
                        PAYMENT_DB)
from app.utils.logger import logger

engine = create_async_engine(
    PAYMENT_DATABASE_URL, echo=False, pool_size=15, max_overflow=0
)
engine_sync = create_engine(PAYMENT_DATABASE_URL_SYNC)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    bonus: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    message: Mapped[str | None] = mapped_column(String, nullable=True)


async def init_db():
    if not database_exists(engine_sync.url):
        logger.info(f"База данных {PAYMENT_DB} не найдена. Создаём базу...")
        create_database(engine_sync.url)
        logger.info(f"База данных {PAYMENT_DB} успешно создана.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def simulate_db_delay():
    rnd = random.random()
    if rnd < 0.1:
        await asyncio.sleep(60)
    elif rnd < 0.2:
        await asyncio.sleep(2)
    else:
        await asyncio.sleep(random.uniform(0.1, 0.3))


async def create_payment_record(
    user_id: int,
    amount: Decimal,
    currency: str,
    status: str,
    message: str,
    session: AsyncSession,
) -> int:
    try:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=status,
            bonus=Decimal("0.00"),
            message=message,
        )
        session.add(payment)
        await session.flush()
        return payment.payment_id
    except Exception as e:
        await session.rollback()
        raise e


async def create_payment_record_v2(
    user_id: int,
    amount: Decimal,
    currency: str,
    status: str,
    message: str,
) -> int:
    async with async_session() as session:

        try:
            payment = Payment(
                user_id=user_id,
                amount=amount,
                currency=currency,
                status=status,
                bonus=Decimal("0.00"),
                message=message,
            )
            session.add(payment)
            await session.commit()
            return payment.payment_id
        except Exception as e:
            await session.rollback()
            raise e


async def update_payment_status(
    payment_id: int, status: str, message: str, bonus: Decimal, session: AsyncSession
):
    try:
        result = await session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = status
            payment.message = message
            payment.bonus = bonus
            session.add(payment)
            await session.flush()
    except Exception as e:
        await session.rollback()
        raise e


async def get_payment_record(payment_id: int, session: AsyncSession):
    result = await session.execute(
        select(Payment).where(Payment.payment_id == payment_id)
    )
    return result.scalar_one_or_none()
