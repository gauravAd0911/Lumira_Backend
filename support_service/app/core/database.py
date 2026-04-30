"""
Database Configuration

- Creates SQLAlchemy engine
- Provides session dependency
- Defines Base for models
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# =========================
# DATABASE ENGINE
# =========================
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # avoids stale connections
    pool_recycle=3600     # fixes MySQL timeout issues
)

# =========================
# SESSION FACTORY
# =========================
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# =========================
# BASE CLASS (IMPORTANT)
# =========================
Base = declarative_base()

# =========================
# DEPENDENCY (FastAPI)
# =========================
def get_db():
    """
    Dependency to get DB session
    Ensures session is closed after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()