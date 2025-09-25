"""Market hours and trading session logic."""

from datetime import datetime, time, timedelta
from src.market.config import MARKET_CONFIG, MARKET_STATUS
from src.market.holidays import is_market_holiday


def get_market_status(eastern_time: datetime) -> str:
    """
    Determine current market status based on Eastern time.

    Args:
        eastern_time: Current time in US/Eastern timezone

    Returns:
        Market status: "pre-market" | "market" | "after-hours" | "closed"
    """
    if not is_trading_day(eastern_time):
        return MARKET_STATUS["CLOSED"]

    current_time = eastern_time.time()

    # Parse configuration times
    premarket_open = time.fromisoformat(MARKET_CONFIG["premarket_open"])
    market_open = time.fromisoformat(MARKET_CONFIG["market_open"])
    market_close = time.fromisoformat(MARKET_CONFIG["market_close"])
    afterhours_close = time.fromisoformat(MARKET_CONFIG["afterhours_close"])

    if premarket_open <= current_time < market_open:
        return MARKET_STATUS["PREMARKET"]
    elif market_open <= current_time < market_close:
        return MARKET_STATUS["MARKET"]
    elif market_close <= current_time < afterhours_close:
        return MARKET_STATUS["AFTERHOURS"]
    else:
        return MARKET_STATUS["CLOSED"]


def is_trading_day(eastern_time: datetime) -> bool:
    """
    Check if the given date is a trading day.

    Args:
        eastern_time: Date to check in Eastern timezone

    Returns:
        True if it's a trading day (not weekend or holiday)
    """
    # Check if weekend (Saturday=5, Sunday=6)
    if eastern_time.weekday() >= 5:
        return False

    # Check if holiday
    return not is_market_holiday(eastern_time)


def get_next_trading_day(eastern_time: datetime) -> datetime:
    """
    Find the next trading day from the given date.

    Args:
        eastern_time: Starting date in Eastern timezone

    Returns:
        Next trading day datetime
    """
    next_day = eastern_time + timedelta(days=1)

    while not is_trading_day(next_day):
        next_day += timedelta(days=1)

    # Set time to market open
    market_open = time.fromisoformat(MARKET_CONFIG["market_open"])
    return next_day.replace(
        hour=market_open.hour,
        minute=market_open.minute,
        second=0,
        microsecond=0
    )