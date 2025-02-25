from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    """
    Модель запроса для создания платежа.
    """

    user_id: int = Field(
        ..., example=1, description="Идентификатор пользователя (кошелёк)"
    )
    amount: Decimal = Field(..., gt=0, example=100.50, description="Сумма платежа")
    currency: str = Field(..., example="USD", description="Валюта платежа")


class PaymentResponse(BaseModel):
    """
    Модель ответа после создания платежа.
    """

    payment_id: int = Field(..., example=1, description="Уникальный ID платежа")
    status: str = Field(
        ..., example="processing", description="Начальный статус платежа"
    )
    message: str = Field(
        ..., example="Платёж в обработке", description="Информация о платеже"
    )


class PaymentStatus(BaseModel):
    """
    Модель для получения состояния платежа.
    """

    payment_id: int = Field(..., example=1, description="Уникальный ID платежа")
    user_id: int = Field(..., example=1, description="Идентификатор пользователя")
    amount: Decimal = Field(..., example=100.50, description="Сумма платежа")
    currency: str = Field(..., example="USD", description="Валюта платежа")
    status: str = Field(..., example="success", description="Итоговый статус платежа")
    bonus: Decimal = Field(
        ..., example=6.00, description="Количество начисленных бонусов"
    )
    message: str = Field(
        ...,
        example="Платёж успешно обработан",
        description="Детальное описание результата платежа",
    )
