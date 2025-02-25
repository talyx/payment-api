import asyncio
from typing import Any, Callable, Coroutine

from app.exception.custom_exception import NoRetryError
from app.utils.logger import logger


async def retry_operation(
    coro: Callable[[], Coroutine[Any, Any, Any]],
    retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2,
) -> Any:
    """
    ### Универсальная функция-ретрайер с экспоненциальной задержкой.

    ### Параметры:
    - **coro**: Корутинная функция, которую нужно выполнить.
    - **retries**: Количество попыток.
    - **delay**: Начальная задержка между попытками.
    - **backoff**: Множитель экспоненциальной задержки.

    ### Возвращает:
    - Результат выполнения корутины или исключение после исчерпания попыток.
    """
    attempt = 0
    current_delay = delay
    while attempt < retries:
        try:
            return await coro()
        except NoRetryError as e:
            raise e
        except Exception as e:
            attempt += 1
            logger.warning(f"Попытка {attempt} завершилась ошибкой: {e}")
            if attempt >= retries:
                logger.error(f"Все попытки исчерпаны: {e}")
                raise e
            await asyncio.sleep(current_delay)
            current_delay *= backoff


async def retry_until_success_service(
    coro: Callable[[], Coroutine[Any, Any, Any]],
    delay: float = 0.5,
    backoff: float = 2,
    max_delay=120.0,
    description="unknown",
) -> Any:
    """
    ### Повторяет вызов корутинной функции до успешного выполнения.

    ### Параметры:
    - **coro**: Корутинная функция, которую нужно выполнить.
    - **delay**: Начальная задержка между попытками.
    - **backoff**: Множитель экспоненциальной задержки.
    - **max_delay**: Максимальная задержка между попытками.
    - **description**: Описание сервиса для логирования.

    ### Возвращает:
    - Результат выполнения корутины или исключение после исчерпания попыток.
    """
    while True:
        try:
            result = await coro()
            if result.get("status") == "success":
                logger.info(f"Сервис {description} выполнен успешно: {result}")
                return result
                break
            else:
                logger.warning(
                    f"Сервис {description} вернул неуспешный ответ: {result}"
                )
        except Exception as e:
            logger.error(f"Ошибка вызова сервиса {description}: {e}")
        logger.info(
            f"Повторная попытка вызова сервиса {description} через {delay:.1f} секунд"
        )
        await asyncio.sleep(delay)
        delay = min(delay * backoff, max_delay)
