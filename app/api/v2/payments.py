import asyncio
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Path

from app.db.payment_db import async_session as payment_async_session
from app.db.payment_db import create_payment_record_v2, get_payment_record
from app.db.user_db import check_user_data
from app.exception.custom_exception import NoRetryError
from app.schemas.models import PaymentRequest, PaymentResponse, PaymentStatus
from app.utils.logger import logger
from app.utils.processes.background import finalize_payment
from app.utils.processes.protected import protected_update_payment_status
from app.utils.processes.retry import retry_operation
from app.utils.services.call_services import (call_loyalty_service,
                                              call_notification_service)

router = APIRouter(prefix="/api/v2", tags=["Платежи v2"])


@router.post(
    "/payments",
    response_model=PaymentResponse,
    summary="Создать платеж",
    responses={
        404: {
            "description": "Пользователь не найден или недостаточно средств",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Пользователь не найден или недостаточно средств"
                    }
                }
            },
        },
        400: {
            "description": "Ошибка создания платежа или проверки пользователя",
            "content": {
                "application/json": {"example": {"detail": "Неизвестная ошибка: ..."}}
            },
        },
        503: {
            "description": "Сервис недоступен",
            "content": {
                "application/json": {
                    "example": {"detail": "Сервис временно недоступен"}
                }
            },
        },
    },
)
async def create_payment_endpoint(
    payment_request: PaymentRequest = Body(
        ..., description="Запрос на создание платежа"
    ),
    background_tasks: BackgroundTasks = None,
) -> PaymentResponse:
    """
    ### Создание платежа

    Принимает запрос в виде модели `PaymentRequest` и возвращает `PaymentResponse`.

    **Процесс:**

    1. **Параллельное выполнение 4-х операций:**
       - Создание записи платежа в базе (с начальным статусом `"processing"` и бонусом 0).
       - Проверка существования пользователя и достаточности его баланса.
       - Вызов внешнего сервиса лояльности для расчёта бонусов.
       - Отправка запроса в сервис уведомлений о получении платежа (со статусом `"processing"`).

    2. Если пользователь не существует или баланс недостаточен, возвращается ошибка.
       Если все операции прошли успешно, возвращается статус `"processing"`.

    В фоне запускается задача, которая:
       - Вычитает сумму с баланса пользователя,
       - Обновляет запись платежа, записывая рассчитанные бонусы,
       - Отправляет финальное уведомление (успех/неудача).
    """
    try:

        async def initial_create_payment():
            return await create_payment_record_v2(
                user_id=payment_request.user_id,
                amount=payment_request.amount,
                currency=payment_request.currency,
                status="processing",
                message="Платёж в обработке",
            )

        task_create_payment = retry_operation(
            initial_create_payment,
            retries=5,
            delay=0.2,
            backoff=2,
        )

        async def initial_check_user():
            return await check_user_data(
                payment_request.user_id, payment_request.amount
            )

        task_check_user = retry_operation(
            initial_check_user,
            retries=5,
            delay=0.2,
            backoff=2,
        )

        async def initial_loyalty():
            return await call_loyalty_service(
                payment_request.user_id,
                payment_request.amount,
            )

        task_loyalty = retry_operation(
            initial_loyalty,
            retries=3,
            delay=0.2,
            backoff=2,
        )

        async def initial_notification():
            return await call_notification_service(
                payment_request.user_id, "processing"
            )

        task_notification = initial_notification()

        results = await asyncio.gather(
            task_create_payment,
            task_check_user,
            task_loyalty,
            task_notification,
            return_exceptions=True,
        )

        (
            payment_record_result,
            user_check_result,
            loyalty_result,
            notification_result,
        ) = results

    except Exception as e:
        logger.error(f"Ошибка запуска параллельных операций: {e}")
        raise HTTPException(status_code=503, detail="Сервис временно недоступен")

    # Обработка результатов:
    if isinstance(payment_record_result, Exception):
        logger.error(f"Ошибка создания платежа: {payment_record_result}")
        raise HTTPException(
            status_code=400, detail=f"Ошибка создания платежа: {payment_record_result}"
        )
    payment_id = payment_record_result

    if isinstance(user_check_result, NoRetryError):
        logger.error(
            f"Пользователь не найден или недостаточно средств: {user_check_result}"
        )
        await protected_update_payment_status(
            payment_id,
            "field",
            f"Пользователь не найден или недостаточно средств {user_check_result}",
        )
        raise HTTPException(
            status_code=404, detail="Пользователь не найден или недостаточно средств"
        )
    elif isinstance(user_check_result, Exception):
        logger.error(f"Ошибка проверки пользователя: {user_check_result}")
        await protected_update_payment_status(
            payment_id, "field", f"Ошибка проверки пользователя: {user_check_result}"
        )
        raise HTTPException(
            status_code=400, detail=f"Ошибка проверки пользователя: {user_check_result}"
        )

    bonus = Decimal("0.00")
    if isinstance(loyalty_result, Exception):
        logger.error(f"Ошибка расчёта бонусов: {loyalty_result}")
    else:
        bonus = Decimal(loyalty_result.get("bonus", 0))

    logger.info(f"Notification result: {notification_result}")

    response = PaymentResponse(
        payment_id=payment_id,
        status="processing",
        message="Платёж в обработке",
    )

    if background_tasks is None:
        background_tasks = BackgroundTasks()

    background_tasks.add_task(
        finalize_payment,
        payment_id,
        payment_request.user_id,
        payment_request.amount,
        payment_request.currency,
        bonus,
    )

    return response


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentStatus,
    summary="Получить статус платежа",
    responses={
        404: {
            "description": "Платёж не найден",
            "content": {
                "application/json": {"example": {"detail": "Платёж не найден"}}
            },
        },
        408: {
            "description": "Время ожидания запроса истекло",
            "content": {
                "application/json": {
                    "example": {"detail": "Время ожидания запроса истекло"}
                }
            },
        },
    },
)
async def get_payment(
    payment_id: int = Path(..., description="Уникальный идентификатор платежа")
) -> PaymentStatus:
    """
    ### Получение состояния платежа по его ID.

    Принимает идентификатор платежа и возвращает его текущий статус.

    **Процесс:**

    1. Поиск записи платежа в базе данных.
    2. Если запись не найдена, возвращается ошибка.
    3. Если запись найдена, возвращается её текущий статус.

    **Ошибки:**

    - Если запись не найдена, возвращается статус 404.
    - Если время ожидания запроса истекло, возвращается статус 408.
    """

    async with payment_async_session(expire_on_commit=False) as payment_session:

        async def fetch_payment():
            return await get_payment_record(payment_id, payment_session)

        try:
            payment = await asyncio.wait_for(
                retry_operation(fetch_payment, retries=3, delay=0.5, backoff=2),
                timeout=5.0,
            )

            if not payment:
                raise HTTPException(status_code=404, detail="Платёж не найден")

            return PaymentStatus(
                payment_id=payment.payment_id,
                user_id=payment.user_id,
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status,
                bonus=payment.bonus,
                message=payment.message,
            )

        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408, detail="Время ожидания запроса истекло"
            )
