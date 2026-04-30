# app/main.py
from fastapi import FastAPI
from app.api.order_routes import router as order_router
from app.core.database import init_db


def create_application() -> FastAPI:
    """
    Application factory function.
    Creates and configures the FastAPI app.
    """

    app = FastAPI(
        title="Order Service API",
        version="1.0.0",
        description="Handles order processing, tracking, and history",
    )

    @app.on_event("startup")
    def startup() -> None:
        """
        Initialize database tables required by the service.
        """
        init_db()

    # Include routers
    app.include_router(order_router)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    def health_check() -> dict:
        """
        Health check endpoint to verify service status.
        """
        return {"status": "OK"}

    return app


# Create app instance
app = create_application()
