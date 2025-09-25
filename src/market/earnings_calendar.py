"""Earnings calendar functionality for TradingAgent MCP Server."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..provider.tradier.client import TradierClient


# Earnings-related event keywords for filtering
EARNINGS_KEYWORDS = [
    "earnings", "quarter", "fiscal year", "results", 
    "quarterly", "annual", "report", "announcement"
]


@dataclass
class EarningsEvent:
    """Earnings event data structure."""
    event: Optional[str]
    begin_date: Optional[str] 
    end_date: Optional[str]
    event_type: Optional[int]
    fiscal_year: Optional[str]
    status: Optional[str]
    estimated_next_date: Optional[str]


@dataclass 
class EarningsCalendarResponse:
    """Comprehensive earnings calendar response."""
    symbol: str
    provider: str
    request_type: str
    earnings_events: List[EarningsEvent]
    total_events: int
    next_earnings_date: Optional[str]
    message: Optional[str]
    error: Optional[str]
    details: Optional[str]


def is_earnings_related(event_description: str) -> bool:
    """Check if an event is earnings-related based on keywords.
    
    Args:
        event_description: The event description text to check
        
    Returns:
        True if the event appears to be earnings-related, False otherwise
    """
    if not event_description:
        return False
        
    return any(
        keyword in event_description.lower() 
        for keyword in EARNINGS_KEYWORDS
    )


def is_recent_event(begin_date: str, cutoff_months: int = 12) -> bool:
    """Check if an event is within the specified time range from current date.
    
    Args:
        begin_date: Event begin date in YYYY-MM-DD format
        cutoff_months: Number of months to look back from current date
        
    Returns:
        True if the event is within the cutoff period, False otherwise
    """
    if not begin_date:
        return False
        
    try:
        event_date = datetime.strptime(begin_date, "%Y-%m-%d")
        cutoff_date = datetime.now() - timedelta(days=cutoff_months * 30)  # Approximate months as 30 days
        return event_date >= cutoff_date
    except (ValueError, TypeError):
        # If date parsing fails, include the event to be safe
        return True


async def get_earnings_calendar(
    symbol: str, 
    tradier_client: Optional[TradierClient] = None
) -> Dict[str, Any]:
    """
    Get corporate calendar information including earnings dates for a security.
    
    Args:
        symbol: Stock symbol to get earnings calendar for
        tradier_client: Tradier client instance (will create if None)
        
    Returns:
        Dictionary containing formatted earnings calendar information
    """
    # Initialize Tradier client if not provided
    if not tradier_client:
        try:
            tradier_client = TradierClient()
        except Exception as e:
            return {
                "error": "Failed to initialize Tradier client",
                "details": str(e),
                "symbol": symbol,
                "provider": "TRADIER",
                "earnings_events": []
            }
    
    try:
        # Get corporate calendar data from Tradier
        calendar_data = tradier_client.get_corporate_calendar(symbol)
        
        if not calendar_data:
            return {
                "symbol": symbol,
                "provider": "TRADIER", 
                "request_type": "Symbol",
                "status": "No calendar data found",
                "earnings_events": [],
                "total_events": 0,
                "next_earnings_date": None,
                "message": f"No calendar data available for {symbol}. This could mean the company doesn't report earnings regularly or the data is not available in Tradier's corporate calendar."
            }
        
        # Extract relevant information
        result = {
            "symbol": symbol,
            "provider": "TRADIER",
            "request_type": calendar_data.get("type", "Symbol"),
            "earnings_events": [],
            "total_events": 0,
            "next_earnings_date": None
        }
        
        # Process results if available
        if "results" in calendar_data and calendar_data["results"]:
            for result_item in calendar_data["results"]:
                if result_item.get("type") == "Company" and "tables" in result_item:
                    tables = result_item["tables"]
                    
                    # Extract corporate calendar events
                    if "corporate_calendars" in tables and tables["corporate_calendars"]:
                        corporate_calendars = tables["corporate_calendars"]
                        
                        # Filter for earnings-related events and recent events (within 1 year)
                        earnings_events = []
                        for event in corporate_calendars:
                            event_description = event.get("event", "")
                            event_begin_date = event.get("begin_date_time", "")
                            
                            # Apply both filters: earnings-related AND recent (within 12 months)
                            if (is_earnings_related(event_description) and 
                                is_recent_event(event_begin_date)):
                                
                                earnings_event = {
                                    "event": event.get("event"),
                                    "begin_date": event.get("begin_date_time"),
                                    "end_date": event.get("end_date_time"),
                                    "event_type": event.get("event_type"),
                                    "fiscal_year": event.get("event_fiscal_year"),
                                    "status": event.get("event_status"),
                                    "estimated_next_date": event.get("estimated_date_for_next_event")
                                }
                                earnings_events.append(earnings_event)
                        
                        # Sort events by date (newest first)
                        earnings_events.sort(
                            key=lambda x: x.get("begin_date", "1970-01-01"), 
                            reverse=True
                        )
                        
                        result["earnings_events"] = earnings_events
                        result["total_events"] = len(earnings_events)
                        
                        # Find next upcoming earnings if available
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        upcoming_events = [
                            event for event in earnings_events 
                            if event.get("begin_date", "1970-01-01") >= current_date
                        ]
                        
                        if upcoming_events:
                            # Get the earliest upcoming event
                            next_event = min(
                                upcoming_events, 
                                key=lambda x: x.get("begin_date", "9999-12-31")
                            )
                            result["next_earnings_date"] = next_event.get("begin_date")
                        else:
                            result["next_earnings_date"] = None
        
        # If no earnings events found, provide a helpful message
        if not result["earnings_events"]:
            result["message"] = (
                f"No earnings events found for {symbol}. This could mean the company doesn't report earnings regularly or the data is not available in Tradier's corporate calendar."
            )
        
        return result
        
    except Exception as e:
        error_result = {
            "error": f"Failed to fetch earnings calendar for {symbol}",
            "details": str(e),
            "symbol": symbol,
            "provider": "TRADIER",
            "earnings_events": [],
            "total_events": 0,
            "next_earnings_date": None
        }
        return error_result