from fastapi import HTTPException


# =========================
# BASE CUSTOM EXCEPTION
# =========================
class AppException(HTTPException):
    """Base application exception with consistent structure."""

    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)


# =========================
# USER EXCEPTIONS
# =========================
class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(404, "User not found")


class UserInactiveException(AppException):
    def __init__(self):
        super().__init__(400, "User is inactive")


# =========================
# ADDRESS EXCEPTIONS
# =========================
class AddressNotFoundException(AppException):
    def __init__(self):
        super().__init__(404, "Address not found")


class AddressLimitExceededException(AppException):
    def __init__(self, limit: int):
        super().__init__(400, f"Address limit exceeded (max {limit})")


class InvalidAddressException(AppException):
    def __init__(self):
        super().__init__(400, "Invalid address data")


class DefaultAddressUpdateException(AppException):
    def __init__(self):
        super().__init__(400, "Unable to update default address")


# =========================
# VALIDATION EXCEPTIONS
# =========================
class InvalidEmailException(AppException):
    def __init__(self):
        super().__init__(400, "Invalid email format")


class InvalidPhoneException(AppException):
    def __init__(self):
        super().__init__(400, "Invalid phone number")


class InvalidPincodeException(AppException):
    def __init__(self):
        super().__init__(400, "Invalid postal code")


class MissingFieldException(AppException):
    def __init__(self, field_name: str):
        super().__init__(400, f"{field_name} is required")


# =========================
# GENERIC EXCEPTIONS
# =========================
class DatabaseException(AppException):
    def __init__(self):
        super().__init__(500, "Database error occurred")


class UnauthorizedException(AppException):
    def __init__(self):
        super().__init__(401, "Unauthorized access")


class ForbiddenException(AppException):
    def __init__(self):
        super().__init__(403, "Forbidden action")