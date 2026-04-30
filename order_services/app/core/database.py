from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

DATABASE_URL = settings.DB_URL or "mysql+pymysql://root:Root@localhost/abt_dev"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Create missing tables for the configured database.
    """
    from app.models.order import Base
    from app.models import order_item, tracking  # noqa: F401

    Base.metadata.create_all(bind=engine)
