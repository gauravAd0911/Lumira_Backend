import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models.cart import Cart
from app.models.order import Order
from app.models.payment import Payment
from app.routers.payment import api_router as payments_api_router
from app.routers.payment import legacy_router as payments_legacy_router

executor = ThreadPoolExecutor(max_workers=1)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, Base.metadata.create_all, engine)
    logger.info("Database tables ready")
    yield


app = FastAPI(
    title="Razorpay Payment API",
    description="Cart -> Order -> Razorpay -> Verify -> DB Update",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_legacy_router, prefix="/payment")
app.include_router(payments_api_router, prefix="/api/v1/payments")

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
def home():
    index = os.path.join(static_path, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"status": "ok", "docs": "/docs"}
