import asyncio
import random
from decimal import Decimal

from fastapi import Body, FastAPI, HTTPException

from app.config import LOYALTY_HOST, LOYALTY_PORT

app = FastAPI(title="External Loyalty Rewards API", version="1.0.0")


@app.post("/loyalty")
async def process_loyalty(
    user_id: str = Body(..., description="ID пользователя"),
    amount: str = Body(..., description="Сумма для начисления баллов"),
):
    bonus = Decimal(amount) * Decimal("0.10")
    print(f"Processing loyalty for user {user_id} with amount {amount}")
    rnd = random.random()
    if rnd < 0.8:
        return {
            "status": "success",
            "message": "Loyalty points awarded",
            "bonus": str(bonus),
        }
    elif rnd < 0.9:
        await asyncio.sleep(60)
        raise HTTPException(status_code=500, detail="Loyalty service error")
    else:
        raise HTTPException(status_code=500, detail="Loyalty service error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=LOYALTY_HOST, port=LOYALTY_PORT)
