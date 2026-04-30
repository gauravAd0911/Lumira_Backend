from enum import Enum


class ReservationStatus(str, Enum):
    """Reservation lifecycle states."""
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"