import asyncio
import random

from fastapi import Body, FastAPI, HTTPException

from app.config import NOTIFICATION_HOST, NOTIFICATION_PORT

app = FastAPI(title="External Notification API", version="1.0.0")


@app.post("/notify")
async def notify(
    user_id: str = Body(..., description="ID пользователя"),
    status: str = Body(..., description="Статус платежа"),
):
    print(f"Sending notification for user {user_id} with status {status}")
    rnd = random.random()
    if rnd < 0.8:
        return {"status": "success", "message": "Notification sent"}
    elif rnd < 0.9:
        await asyncio.sleep(60)
        raise HTTPException(status_code=500, detail="Notification service error")
    else:
        raise HTTPException(status_code=500, detail="Notification service error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=NOTIFICATION_HOST, port=NOTIFICATION_PORT)
