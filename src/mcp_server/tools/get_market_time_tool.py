"""MCP tool for market time and status information."""

from datetime import datetime, timezone
from typing import Dict, Any
from src.utils.time import get_timezone_time
from src.market.hours import get_market_status, is_trading_day, get_next_trading_day
from src.market.config import MARKET_CONFIG


async def get_market_time_status() -> Dict[str, Any]:
    """
    Get current market time and status information.

    This MCP tool provides comprehensive market timing information including:
    - Current US Eastern time
    - Market session status (pre-market, market, after-hours, closed)
    - Trading day indicator
    - Next trading day (if currently non-trading)

    Returns:
        Dictionary containing:
        - eastern_time: Current time in US/Eastern (ISO format)
        - market_status: Current market session status
        - is_trading_day: Boolean indicating if today is a trading day
        - timestamp: UTC timestamp of this response
        - next_trading_day: Next trading day (if not trading day)
    """
    try:
        eastern_time = get_timezone_time(MARKET_CONFIG["timezone"])

        result = {
            "eastern_time": eastern_time.isoformat(),
            "market_status": get_market_status(eastern_time),
            "is_trading_day": is_trading_day(eastern_time),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Add next trading day if current day is not a trading day
        if not result["is_trading_day"]:
            next_day = get_next_trading_day(eastern_time)
            result["next_trading_day"] = next_day.date().isoformat()

        return result

    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }