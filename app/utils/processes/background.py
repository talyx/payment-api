import asyncio
from decimal import Decimal

from app.utils.logger import logger
from app.utils.processes.protected import (protected_process_transaction,
                                           protected_update_payment_status)
from app.utils.processes.retry import retry_until_success_service
from app.utils.services.call_services import (call_loyalty_service,
                                              call_notification_service)


async def process_payment(
    payment_id: int,
    user_id: int,
    amount: Decimal,
    currency: str,
) -> None:
    """
    ### Фоновая функция обработки платежа.

    В рамках транзакции в базе пользователей проверяется наличие достаточных средств на кошельке.
    Если средств достаточно, они списываются, и статус платежа обновляется.
    Если обновление статуса успешно, транзакция коммитится, и вызываются внешние сервисы.
    Сервис уведомлений запускается один раз без ретраев.
    Сервис лояльности запускается в фоновом режиме и повторяется до достижения успеха.

    ### Параметры:
    - **payment_id**: ID платежа.
    - **user_id**: ID пользователя.
    - **amount**: Сумма платежа.
    - **currency**: Валюта платежа.
    """
    logger.info(f"Начало обработки платежа {payment_id}")

    try:
        await protected_process_transaction(
            payment_id, user_id, amount, Decimal("0.00")
        )
        try:
            await call_notification_service(user_id, "success")
        except Exception as e:
            logger.warning(
                f"Сервис уведомлений вернул ошибку для платежа {payment_id}: {e}"
            )

        async def call_loyalty():
            return await call_loyalty_service(user_id, amount)

        asyncio.create_task(
            retry_until_success_service(
                coro=call_loyalty,
                description=f"loyalty-payment_id:{payment_id}",
            )
        )
    except Exception as e:
        logger.error(f"Ошибка обработки платежа {payment_id}: {e}")
        await protected_update_payment_status(
            payment_id, "failed", f"Ошибка обработки платежа:{str(e)}", Decimal("0.00")
        )


async def finalize_payment(
    payment_id: int, user_id: int, amount: Decimal, currency: str, bonus: Decimal
):
    """
    ### Фоновая задача для финальной обработки платежа.

    - Вычитает сумму с баланса пользователя.
    - Обновляет запись платежа, устанавливая количество бонусов.
    - Выполняет ретрай начисления бонусов до успешного результата.
    - Отправляет финальное уведомление с итоговым статусом.

    ### Параметры:
    - **payment_id**: ID платежа.
    - **user_id**: ID пользователя.
    - **amount**: Сумма платежа.
    - **currency**: Валюта платежа.
    - **bonus**: Количество бонусов.
    """
    logger.info(f"Начало фоновой обработки платежа {payment_id}")
    try:
        await protected_process_transaction(payment_id, user_id, amount, bonus)

        try:
            await call_notification_service(user_id, "success")
        except Exception as e:
            logger.warning(
                f"Ошибка отправки финального уведомления для платежа {payment_id}: {e}"
            )

        if bonus == Decimal("0.00"):

            async def call_loyalty():
                return await call_loyalty_service(user_id, amount)

            loyalty_response = await asyncio.create_task(
                retry_until_success_service(
                    coro=call_loyalty,
                    description=f"loyalty-payment_id:{payment_id}",
                )
            )

            bonus = Decimal(loyalty_response.get("bonus", 0))
            await protected_update_payment_status(
                payment_id,
                "success",
                "Фоновая операция по зачислению бонусов прошла успешно.",
                bonus,
            )

    except Exception as e:
        logger.error(f"Ошибка обработки платежа {payment_id}: {e}")
        await protected_update_payment_status(
            payment_id, "failed", f"Ошибка обработки платежа:{str(e)}"
        )
