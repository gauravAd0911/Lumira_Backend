"""Pydantic request/response schemas for the Review Service API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import RATING_MAX, RATING_MIN


# --------------------------------------------------------------------------- #
# Shared / base
# --------------------------------------------------------------------------- #


class ReviewBase(BaseModel):
    """Fields shared by create and patch schemas."""

    rating: int = Field(..., ge=RATING_MIN, le=RATING_MAX, description="Star rating 1–5")
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)

    @field_validator("title", "body", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """Strip leading/trailing whitespace from text fields."""
        return value.strip()


# --------------------------------------------------------------------------- #
# Request schemas
# --------------------------------------------------------------------------- #


class ReviewCreateRequest(ReviewBase):
    """Payload for POST /products/{product_id}/reviews."""


class ReviewPatchRequest(BaseModel):
    """Payload for PATCH /reviews/{review_id} — all fields optional."""

    rating: int | None = Field(None, ge=RATING_MIN, le=RATING_MAX)
    title: str | None = Field(None, min_length=1, max_length=255)
    body: str | None = Field(None, min_length=1)

    @field_validator("title", "body", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        """Strip leading/trailing whitespace from optional text fields."""
        return value.strip() if isinstance(value, str) else value


# --------------------------------------------------------------------------- #
# Response schemas
# --------------------------------------------------------------------------- #


class ReviewResponse(BaseModel):
    """Full review representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    review_id: str
    product_id: str
    user_id: str
    rating: int
    title: str
    body: str
    is_verified: bool
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedReviewsResponse(BaseModel):
    """Paginated list of reviews with metadata."""

    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RatingSummaryResponse(BaseModel):
    """Aggregated rating breakdown for a product."""

    product_id: str
    total_reviews: int
    average_rating: float
    five_star: int
    four_star: int
    three_star: int
    two_star: int
    one_star: int
    verified_count: int


class ReviewEligibilityResponse(BaseModel):
    """Whether the current user can review a product."""

    can_review: bool
    reason: str | None = None
