import os
from fastapi import FastAPI
from app.api.v1.endpoints import user, address
from app.db.base import Base
from app.db.models.user import User
from app.db.session import SessionLocal, engine
from app.dependencies.auth import get_current_user_id

app = FastAPI(title="User Profile Service")

# ✅ AUTO CREATE TABLES (VERY IMPORTANT)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    # Seed a mock user so `/api/v1/users/me` works with mock auth in dev mode.
    if os.getenv("DEBUG", "").strip().lower() in {"1", "true", "yes", "y"}:
        db = SessionLocal()
        try:
            mock_user_id = get_current_user_id()
            existing = db.query(User).filter(User.id == mock_user_id).first()
            if not existing:
                db.add(
                    User(
                        id=mock_user_id,
                        email="mock.user@example.com",
                        full_name="Mock User",
                        phone=None,
                        is_active=True,
                    )
                )
                db.commit()
        finally:
            db.close()

# ✅ Include routers
app.include_router(user.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(address.router, prefix="/api/v1/users/me/addresses", tags=["Addresses"])
