from decimal import Decimal

import httpx

from app.config import LOYALTY_SERVICE_URL, NOTIFICATION_SERVICE_URL


async def call_loyalty_service(user_id: int, amount: Decimal) -> dict:
    """
    ### Вызов внешнего сервиса для начисления бонусов (loyalty).

    ### params:
        user_id: ID пользователя.
        amount: Сумма платежа.

    ### return:
        Ответ сервиса в виде словаря.
    """
    async with httpx.AsyncClient(timeout=5) as client:

        async def do_call() -> dict:
            response = await client.post(
                LOYALTY_SERVICE_URL,
                json={
                    "user_id": str(user_id),
                    "amount": str(amount),
                },
            )
            response.raise_for_status()
            return response.json()

        return await do_call()


async def call_notification_service(user_id: int, status: str) -> dict:
    """
    ### Вызов внешнего сервиса для отправки уведомлений (notification).

    ### params:
        user_id: ID пользователя.
        status: Текущий статус платежа.

    ### return:
        Ответ сервиса в виде словаря.
    """
    async with httpx.AsyncClient(timeout=5) as client:

        async def do_call() -> dict:
            response = await client.post(
                NOTIFICATION_SERVICE_URL,
                json={
                    "user_id": str(user_id),
                    "status": status,
                },
            )
            response.raise_for_status()
            return response.json()

        return await do_call()
