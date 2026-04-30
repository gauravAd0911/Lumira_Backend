from fastapi import FastAPI
from app.database import init_db
from app.routes.notification_routes import router

app = FastAPI(title="Notification Service")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(router)
