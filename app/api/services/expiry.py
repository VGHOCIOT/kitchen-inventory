from enum import Enum
from datetime import datetime

from models.item import Locations


class ExpiryStatus(str, Enum):
    GOOD = "good"
    NEARING = "nearing"
    EXPIRED = "expired"


NEARING_THRESHOLDS = {
    Locations.FRIDGE: 3,
    Locations.FREEZER: 30,
    Locations.CUPBOARD: 7,
}


def compute_expiry_status(expires_at: datetime | None, location: Locations) -> ExpiryStatus | None:
    if expires_at is None:
        return None
    days = (expires_at.date() - datetime.utcnow().date()).days
    threshold = NEARING_THRESHOLDS.get(location, 7)
    if days < 0:
        return ExpiryStatus.EXPIRED
    if days <= threshold:
        return ExpiryStatus.NEARING
    return ExpiryStatus.GOOD
