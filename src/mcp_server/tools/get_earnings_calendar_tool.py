"""MCP tool for earnings calendar information retrieval."""

from typing import Dict, Any
from datetime import datetime, timezone
from src.market.earnings_calendar import get_earnings_calendar
from src.provider.tradier.client import TradierClient


async def get_earnings_calendar_tool(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive earnings calendar information for a stock symbol.
    
    This MCP tool retrieves detailed earnings calendar data including:
    - Upcoming earnings announcement dates
    - Historical earnings events and calls
    - Corporate calendar information
    - Next earnings date estimation
    - Event details (dates, fiscal year, status)
    
    The information is sourced from real-time Tradier API data and provides
    both structured data for programmatic use and comprehensive event details
    for trading and investment analysis.
    
    Args:
        symbol: Stock ticker symbol (e.g., "TSLA", "AAPL", "NVDA")
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if request succeeded
        - symbol: The requested stock symbol (normalized to uppercase)
        - provider: Data provider used ("TRADIER")
        - earnings_events: List of earnings-related events with details
        - total_events: Number of earnings events found
        - next_earnings_date: Next upcoming earnings date (if available)
        - message: Informational message (if applicable)
        - timestamp: UTC timestamp of the response
        - error: Error message (only present if failed)
        
    Examples:
        >>> result = await get_earnings_calendar_tool("AAPL")
        >>> print(f"Next earnings: {result['next_earnings_date']}")
        Next earnings: 2024-01-25
        
        >>> for event in result['earnings_events']:
        ...     print(f"{event['event']} on {event['begin_date']}")
        Q1 2024 Earnings Call on 2024-01-25
        Q4 2023 Results on 2023-10-26
    """
    try:
        # Normalize symbol to uppercase
        normalized_symbol = symbol.upper().strip()
        
        # Initialize Tradier client
        tradier_client = TradierClient()
        
        # Get earnings calendar data
        calendar_data = await get_earnings_calendar(normalized_symbol, tradier_client)
        
        # Generate response timestamp
        response_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Check if the request was successful (no error in the response)
        if "error" in calendar_data:
            return {
                "success": False,
                "symbol": normalized_symbol,
                "provider": calendar_data.get("provider", "TRADIER"),
                "error": calendar_data["error"],
                "details": calendar_data.get("details", ""),
                "timestamp": response_timestamp,
                "earnings_events": [],
                "total_events": 0,
                "next_earnings_date": None
            }
        
        # Successful response
        return {
            "success": True,
            "symbol": normalized_symbol,
            "provider": calendar_data.get("provider", "TRADIER"),
            "request_type": calendar_data.get("request_type", "Symbol"),
            "earnings_events": calendar_data.get("earnings_events", []),
            "total_events": calendar_data.get("total_events", 0),
            "next_earnings_date": calendar_data.get("next_earnings_date"),
            "message": calendar_data.get("message"),
            "timestamp": response_timestamp
        }
        
    except Exception as e:
        # Handle any errors gracefully
        error_timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": False,
            "symbol": symbol.upper().strip() if symbol else "UNKNOWN",
            "provider": "TRADIER", 
            "error": f"Failed to fetch earnings calendar for {symbol}",
            "details": str(e),
            "timestamp": error_timestamp,
            "earnings_events": [],
            "total_events": 0,
            "next_earnings_date": None
        }