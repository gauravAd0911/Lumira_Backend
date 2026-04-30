"""Application-specific exception hierarchy."""


class ReviewServiceError(Exception):
    """Base exception for all Review Service errors."""


class NotFoundError(ReviewServiceError):
    """Raised when a requested resource does not exist."""


class ForbiddenError(ReviewServiceError):
    """Raised when the caller is not authorised to perform an action."""


class ConflictError(ReviewServiceError):
    """Raised when an action violates a uniqueness constraint."""


class EligibilityError(ReviewServiceError):
    """Raised when a user does not meet the verified-purchaser requirement."""