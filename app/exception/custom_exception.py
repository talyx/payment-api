class MyCustomError(Exception):
    """Исключение, сигнализирующее о специфической ошибке в приложении."""

    pass


class NoRetryError(MyCustomError):
    """Исключение, сигнализирующее о том, что повторная попытка выполнения операции бессмысленна."""

    pass


class UserNotFoundError(NoRetryError):
    """Исключение, сигнализирующее о том, что пользователь не найден в базе данных."""

    def __init__(self, message: str = "User not found", code: int = None):
        super().__init__(message)
        self.code = code


class NotEnoughMoney(NoRetryError):
    """Исключение, сигнализирующее о том, что у пользователя не достаточно средств в кошельке."""

    def __init__(self, message: str, code: int = None):
        super().__init__(message)
        self.code = code
