from fastapi import FastAPI
from app.api.v1.inventory_routes import router as inventory_router

app = FastAPI(title="Inventory Service")


@app.get("/")
def health_check():
    return {"status": "ok"}


# 🔥 THIS LINE IS MISSING IN YOUR CASE
app.include_router(inventory_router)