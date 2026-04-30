"""SQLAlchemy ORM models for the Review Service."""
import uuid
from datetime import datetime
 
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey,
    Index, JSON, SmallInteger, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
 
 
class Base(DeclarativeBase):
    pass
 
 
class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="product", lazy="noload")
 
 
class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user", lazy="noload")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", lazy="noload")
 
 
class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_product", "user_id", "product_id"),
        Index("idx_orders_status", "status"),
    )
    order_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship("User", back_populates="orders", lazy="noload")
    product: Mapped["Product"] = relationship("Product", lazy="noload")
 
 
class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="chk_reviews_rating"),
        CheckConstraint("status IN ('PUBLISHED','HIDDEN','DELETED')", name="chk_reviews_status"),
        Index("idx_reviews_product_created", "product_id", "created_at"),
        Index("idx_reviews_user", "user_id"),
        Index("idx_reviews_status", "status"),
        Index("idx_reviews_rating", "rating"),
    )
    review_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PUBLISHED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product: Mapped["Product"] = relationship("Product", back_populates="reviews", lazy="noload")
    user: Mapped["User"] = relationship("User", back_populates="reviews", lazy="noload")
 
 
class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (Index("idx_outbox_status_created", "status", "created_at"),)
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)