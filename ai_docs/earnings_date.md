# Reference Implementation for Earnings Calendar

```python
"""
Earnings calendar functionality for MCP Option Wheel Strategy Server
"""

import json
from datetime import datetime
from typing import Optional

from ..providers.tradier_client import TradierClient


async def get_earnings_calendar(symbol: str, provider: str, tradier_client: Optional[TradierClient] = None) -> str:
    """
    Get corporate calendar information including earnings dates for a security.

    Args:
        symbol: Stock symbol to get earnings calendar for
        provider: Data provider ('TRADIER' or 'ALPACA')
        tradier_client: Tradier client instance if using TRADIER provider

    Returns:
        JSON string with formatted earnings calendar information
    """

    if provider != "TRADIER" or not tradier_client:
        return json.dumps(
            {
                "error": "Earnings calendar data is only available with TRADIER provider",
                "symbol": symbol,
                "provider": provider,
            },
            indent=2,
        )

    try:
        # Get corporate calendar data from Tradier
        calendar_data = tradier_client.get_corporate_calendar(symbol)

        if not calendar_data:
            return json.dumps(
                {"symbol": symbol, "provider": "TRADIER", "status": "No calendar data found", "earnings_events": []},
                indent=2,
            )

        # Extract relevant information
        result = {
            "symbol": symbol,
            "provider": "TRADIER",
            "request_type": calendar_data.get("type", "Symbol"),
            "earnings_events": [],
        }

        # Process results if available
        if "results" in calendar_data and calendar_data["results"]:
            for result_item in calendar_data["results"]:
                if result_item.get("type") == "Company" and "tables" in result_item:
                    tables = result_item["tables"]

                    # Extract corporate calendar events
                    if "corporate_calendars" in tables and tables["corporate_calendars"]:
                        corporate_calendars = tables["corporate_calendars"]

                        # Filter for earnings-related events
                        earnings_events = []
                        for event in corporate_calendars:
                            event_description = event.get("event", "").lower()
                            if any(
                                keyword in event_description
                                for keyword in ["earnings", "quarter", "fiscal year", "results"]
                            ):
                                earnings_event = {
                                    "event": event.get("event"),
                                    "begin_date": event.get("begin_date_time"),
                                    "end_date": event.get("end_date_time"),
                                    "event_type": event.get("event_type"),
                                    "fiscal_year": event.get("event_fiscal_year"),
                                    "status": event.get("event_status"),
                                    "estimated_next_date": event.get("estimated_date_for_next_event"),
                                }
                                earnings_events.append(earnings_event)

                        # Sort events by date (newest first)
                        earnings_events.sort(key=lambda x: x.get("begin_date", "1970-01-01"), reverse=True)

                        result["earnings_events"] = earnings_events
                        result["total_events"] = len(earnings_events)

                        # Find next upcoming earnings if available
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        upcoming_events = [
                            event for event in earnings_events if event.get("begin_date", "1970-01-01") >= current_date
                        ]

                        if upcoming_events:
                            result["next_earnings_date"] = min(
                                upcoming_events, key=lambda x: x.get("begin_date", "9999-12-31")
                            ).get("begin_date")
                        else:
                            result["next_earnings_date"] = "Not available"

        # If no earnings events found, provide a helpful message
        if not result["earnings_events"]:
            result["message"] = (
                f"No earnings events found for {symbol}. This could mean the company doesn't report earnings regularly or the data is not available in Tradier's corporate calendar."
            )

        return json.dumps(result, indent=2)

    except Exception as e:
        error_result = {
            "error": f"Failed to fetch earnings calendar for {symbol}",
            "details": str(e),
            "symbol": symbol,
            "provider": provider,
        }
        return json.dumps(error_result, indent=2)

```
