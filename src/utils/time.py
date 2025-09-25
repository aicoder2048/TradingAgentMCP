"""General-purpose time utilities."""

from datetime import datetime
from zoneinfo import ZoneInfo


def get_timezone_time(timezone: str = "UTC") -> datetime:
    """
    Get current time in specified timezone.

    Args:
        timezone: IANA timezone string (e.g., "US/Eastern", "UTC", "Asia/Shanghai")

    Returns:
        Current datetime in the specified timezone

    Raises:
        ZoneInfoNotFoundError: If timezone is invalid
    """
    return datetime.now(ZoneInfo(timezone))