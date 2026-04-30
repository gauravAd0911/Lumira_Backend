from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }