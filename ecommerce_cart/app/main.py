from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import cart, products

# Auto-create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🛒 Ecommerce Cart API

A production-ready shopping cart service built with **FastAPI** and **MySQL**.

### Cart Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cart` | Fetch current user's cart |
| `POST` | `/api/cart/items` | Add a product to the cart |
| `PUT` | `/api/cart/items/{product_id}` | Update item quantity |
| `DELETE` | `/api/cart/items/{product_id}` | Remove a specific item |
| `DELETE` | `/api/cart` | Clear entire cart |

### Authentication
Pass `X-User-Id` header to identify the user (replace with JWT in production).
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(cart.router)
app.include_router(products.router)


def _error_payload(*, code: str, message: str, details=None):
    return {
        "success": False,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        },
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and {"success", "message", "error"} <= set(detail.keys()):
        payload = detail
    else:
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
        }
        payload = _error_payload(
            code=code_map.get(exc.status_code, "SERVER_ERROR"),
            message=str(detail),
        )
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            code="VALIDATION_ERROR",
            message="Please correct the highlighted details.",
            details=[
                {
                    "field": str(error.get("loc", ["request"])[-1]),
                    "message": error.get("msg", "Invalid value."),
                }
                for error in exc.errors()
            ],
        ),
    )


@app.get("/", tags=["Health"])
def health_check():
    return {
        "success": True,
        "message": "Cart service is healthy.",
        "data": {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
        "error": None,
    }
