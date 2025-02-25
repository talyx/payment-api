from fastapi import FastAPI

from app.api.v1.payments import router as payments_router
from app.api.v2.payments import router as payments_router_v2
from app.utils.api.lifespan import lifespan

app = FastAPI(
    lifespan=lifespan,
    title="Основной сервис оплаты",
    description="Сервис для обработки платежей с асинхронными вызовами к разным базам данных и внешним сервисам (loyalty и notification)",
    version="2.0.0",
)

app.include_router(payments_router)
app.include_router(payments_router_v2)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2)
