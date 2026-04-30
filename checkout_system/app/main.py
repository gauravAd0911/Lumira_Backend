import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routers import checkout, guest_checkout, guest_orders, products

cfg = get_settings()

app = FastAPI(
    title=cfg.app_name,
    version="2.0.0",
    description="""
## Guest Checkout — Dual OTP (Email + WhatsApp)

### Checkout flow
1. `POST /api/v1/guest-checkout/request-verification` — send OTPs to email and WhatsApp
2. `POST /api/v1/guest-checkout/verify` — verify email OTP
3. `POST /api/v1/guest-checkout/verify` — verify WhatsApp OTP → receive `session_token`
4. `POST /api/v1/guest-orders` — place order using `session_token`

### Order lookup flow
1. `POST /api/v1/guest-orders/request-lookup` — send email OTP
2. `POST /api/v1/guest-orders/verify-lookup`  — verify → receive order list
""",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guest_checkout.router)
app.include_router(guest_orders.router)
app.include_router(products.router)
app.include_router(checkout.router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)

_static = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static):
    app.mount("/static", StaticFiles(directory=_static), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def storefront():
    tpl = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(tpl):
        return HTMLResponse(open(tpl).read())
    return HTMLResponse("<h1>ShopFlow</h1><a href='/docs'>API Docs →</a>")
