from decimal import Decimal

from app.db.payment_db import async_session as payment_async_session
from app.db.payment_db import update_payment_status
from app.db.user_db import async_session as user_async_session
from app.db.user_db import update_user_balance
from app.exception.custom_exception import NotEnoughMoney, UserNotFoundError
from app.utils.logger import logger
from app.utils.processes.retry import retry_operation


async def protected_update_payment_status(
    payment_id: int, status: str, message: str, bonus: Decimal = Decimal("0.00")
):
    """
    Обновляет статус платежа с защитой от ошибок.

    ### Параметры:
    - **payment_id**: ID платежа.
    - **status**: Новый статус платежа.
    - **message**: Сообщение о статусе.
    """
    async with payment_async_session() as payment_session:
        try:

            async def update():
                return await update_payment_status(
                    payment_id, status, message, bonus, payment_session
                )

            await retry_operation(update, 3, 0.2, 2)

            await payment_session.commit()
            logger.info(f"Статус платежа {payment_id} успешно обновлен на {status}")
        except Exception as e:
            await payment_session.rollback()
            logger.error(f"Ошибка при обновлении статуса платежа {payment_id}: {e}")
            raise e


async def protected_process_transaction(
    payment_id: int, user_id: int, amount: Decimal, bonus: Decimal
):
    """
    Обрабатывает транзакцию с защитой от ошибок.

    ### Параметры:
    - **payment_id**: ID платежа.
    - **user_id**: ID пользователя.
    - **amount**: Сумма транзакции.
    """
    async with user_async_session() as user_session:
        try:

            async def update():
                await update_user_balance(user_id, amount, user_session)

            await retry_operation(update, 5, 0.5, 2)
            await protected_update_payment_status(
                payment_id, "success", "Платеж успешно обработан", bonus
            )
            await user_session.commit()
            logger.info(f"Баланс пользователя {user_id} успешно обновлен")
        except (UserNotFoundError, NotEnoughMoney) as e:
            await user_session.rollback()
            logger.info(f"Ошибка обновления баланса: {e}")
            raise e
        except Exception as e:
            await user_session.rollback()
            logger.error(f"Необработанная ошибка при обновлении баланса: {e}")
            raise Exception(f"Необработанная ошибка при обновлении баланса: {e}")
