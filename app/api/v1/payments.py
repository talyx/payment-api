import asyncio

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Path

from app.db.payment_db import async_session as payment_async_session
from app.db.payment_db import create_payment_record, get_payment_record
from app.schemas.models import PaymentRequest, PaymentResponse, PaymentStatus
from app.utils.processes.background import process_payment
from app.utils.processes.retry import retry_operation

router = APIRouter(prefix="/api/v1", tags=["Платежи v1"])


@router.post(
    "/payments",
    response_model=PaymentResponse,
    summary="Создать платеж",
    responses={
        400: {
            "description": "Ошибка базы данных",
            "content": {
                "application/json": {"example": {"detail": "Ошибка базы данных"}}
            },
        },
        503: {
            "description": "Сервис недоступен",
            "content": {
                "application/json": {
                    "example": {"detail": "Сервис недоступен(таймаут)"}
                }
            },
        },
    },
)
async def create_payment(
    payment_request: PaymentRequest = Body(
        ..., description="Запрос на создание платежа"
    ),
    background_tasks: BackgroundTasks = None,
) -> PaymentResponse:
    """
    ### Создание платежа

    Принимает запрос в виде модели `PaymentRequest` и возвращает `PaymentResponse`.

    **Процесс:**
    1. Создаётся запись платежа со статусом "processing".
    2. Возвращается ответ с идентификатором платежа и статусом "processing".
    3. В фоне запускается задача для обработки платежа:
        - Проверяется баланс пользователя.
        - Обновляется запись платежа.
        - Вызываются внешние сервисы.

    """

    try:
        async with payment_async_session() as payment_session:

            async def create_payment_op():
                return await create_payment_record(
                    user_id=payment_request.user_id,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    status="processing",
                    message="Платёж в обработке",
                    session=payment_session,
                )

            payment_id = await asyncio.wait_for(
                retry_operation(
                    coro=create_payment_op, retries=5, delay=0.2, backoff=2
                ),
                timeout=5.0,
            )

            await payment_session.commit()

    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Сервис временно недоступен")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Неизвестная ошибка: {e}")

    background_tasks.add_task(
        process_payment,
        payment_id,
        payment_request.user_id,
        payment_request.amount,
        payment_request.currency,
    )

    return PaymentResponse(
        payment_id=payment_id, status="processing", message="Платёж в обработке"
    )


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
