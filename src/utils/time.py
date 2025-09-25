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


def get_market_time_et() -> datetime:
    """
    Get current US market time in Eastern Time.
    
    US financial markets operate in Eastern Time (ET), which is 
    US/Eastern timezone (automatically handles EST/EDT transitions).
    
    Returns:
        Current datetime in US Eastern Time
    """
    return get_timezone_time("US/Eastern")