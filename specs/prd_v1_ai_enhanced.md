# Trading Agent MCP Server - Enhanced Product Requirements Document v1

## Executive Summary

This document outlines the implementation plan for a Trading Agent MCP Server that provides market time synchronization and status functionality. The server will be used by Claude Code, which is a Trading Agent Instance, operating as a primary agent with its own context window for trading operations.

## Problem Statement

Trading agents operating in different time zones need reliable, synchronized access to US market time information and trading session status. Without proper time alignment and market status awareness, trading decisions may be made based on incorrect assumptions about market availability, leading to failed trades or missed opportunities.

## Objectives

1. **Primary Goal**: Create an MCP Server tool that provides accurate US Eastern time and market session status
2. **Architectural Goal**: Establish a clean, modular architecture that separates general utilities, market-specific logic, and MCP-specific implementations
3. **Extensibility Goal**: Build a foundation that can easily accommodate future trading features like broker integration, data providers, and trading strategies

## Technical Architecture

### Core Design Principles

1. **Separation of Concerns**: Clear boundaries between utility functions, business logic, and MCP implementations
2. **Configuration-Driven**: Centralized configuration for market parameters
3. **Minimal Implementation**: Only implement functions that are actually used
4. **English-First**: All status values and constants in English for international compatibility
5. **Tool Naming Convention**: MCP tools use `*_tool.py` suffix, prompts use `*_prompt.py` suffix

### Directory Structure

```
src/
├── utils/                              # General-purpose utilities
│   ├── __init__.py
│   └── time.py                        # Timezone utilities
│       └── get_timezone_time()
│
├── market/                            # Market-specific business logic
│   ├── __init__.py
│   ├── config.py                     # Market configuration constants
│   ├── hours.py                      # Market hours and status logic
│   │   ├── get_market_status()
│   │   ├── is_trading_day()
│   │   └── get_next_trading_day()
│   ├── holidays.py                   # Holiday management
│   │   ├── load_holidays()
│   │   └── is_market_holiday()
│   └── data/                         # Market data files
│       └── mkt_holidays_2025_2026.json
│
└── mcp_server/                        # MCP Server specific code
    ├── __init__.py
    ├── server.py                      # Server registration and setup
    ├── config/
    │   └── settings.py               # MCP-specific configuration
    ├── tools/                        # MCP Tools
    │   ├── __init__.py
    │   ├── hello_tool.py            # Example tool (existing)
    │   └── get_market_time_tool.py  # Market time status tool
    │       └── get_market_time()
    └── prompts/                      # MCP Prompts (future)
        └── __init__.py
```

## Implementation Details

### Phase 1: Utility Layer Implementation

#### `src/utils/time.py`

```python
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
```

### Phase 2: Market Business Logic Layer

#### `src/market/config.py`

```python
"""Market configuration constants."""

MARKET_CONFIG = {
    "timezone": "US/Eastern",
    "market_open": "09:30",
    "market_close": "16:00",
    "premarket_open": "04:00",
    "afterhours_close": "20:00"
}

MARKET_STATUS = {
    "PREMARKET": "pre-market",
    "MARKET": "market",
    "AFTERHOURS": "after-hours",
    "CLOSED": "closed"
}
```

#### `src/market/holidays.py`

```python
"""Holiday management for US stock market."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Set, Optional

_HOLIDAYS_CACHE: dict[str, Set[date]] = {}

def load_holidays(year_range: str) -> Set[date]:
    """
    Load holidays for a specific year range.

    Args:
        year_range: Year range string (e.g., "2024_2025")

    Returns:
        Set of holiday dates
    """
    if year_range in _HOLIDAYS_CACHE:
        return _HOLIDAYS_CACHE[year_range]

    data_dir = Path(__file__).parent / "data"
    file_path = data_dir / f"mkt_holidays_{year_range}.json"

    with open(file_path, 'r') as f:
        data = json.load(f)
        holidays = {
            datetime.strptime(h["date"], "%Y-%m-%d").date()
            for h in data["holidays"]
        }

    _HOLIDAYS_CACHE[year_range] = holidays
    return holidays

def is_market_holiday(check_date: datetime) -> bool:
    """
    Check if a given date is a US market holiday.

    Args:
        check_date: Date to check

    Returns:
        True if the date is a market holiday
    """
    year = check_date.year

    # Determine which holiday file to use
    if year == 2025 or year == 2026:
        year_range = "2025_2026"
    else:
        # For years outside our data, return False
        return False

    holidays = load_holidays(year_range)
    return check_date.date() in holidays
```

#### `src/market/hours.py`

```python
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
```

### Phase 3: MCP Tool Implementation

#### `src/mcp_server/tools/get_market_time_tool.py`

```python
"""MCP tool for market time and status information."""

from datetime import datetime
from typing import Dict, Any
from src.utils.time import get_timezone_time
from src.market.hours import get_market_status, is_trading_day, get_next_trading_day
from src.market.config import MARKET_CONFIG

async def get_market_time_tool() -> Dict[str, Any]:
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
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Add next trading day if current day is not a trading day
        if not result["is_trading_day"]:
            next_day = get_next_trading_day(eastern_time)
            result["next_trading_day"] = next_day.date().isoformat()

        return result

    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
```

### Phase 4: Server Registration

#### Update `src/mcp_server/server.py`

```python
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from typing import Dict, Any
from .tools.hello_tool import hello
from .tools.market_time_tool import get_market_time_status
from .prompts.hello_prompt import call_hello_multiple
from .config.settings import settings

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Server lifecycle management."""
    print(f"🚀 Starting {settings.server_name} server...")
    yield
    print(f"👋 Shutting down {settings.server_name} server...")

def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name=settings.server_name,
        version=settings.version,
        lifespan=lifespan
    )

    @mcp.tool()
    async def hello_tool(name: str) -> Dict[str, Any]:
        """Say hello to someone."""
        return await hello(name)

    @mcp.tool()
    async def market_time_status_tool() -> Dict[str, Any]:
        """
        Get current US market time and trading status.

        Returns comprehensive market timing information including Eastern time,
        market session status, and trading day information.
        """
        return await get_market_time_status()

    @mcp.prompt()
    async def call_hello_multiple_prompt(name: str, times: int = 3) -> str:
        """Generate a prompt to call hello multiple times."""
        return await call_hello_multiple(name, times)

    return mcp
```

## Data Files

### `src/market/data/mkt_holidays_2025_2026.json`

```json
{
  "year_range": "2025-2026",
  "holidays": [
    {"date": "2025-01-01", "name": "New Year's Day"},
    {"date": "2025-01-20", "name": "Martin Luther King Jr. Day"},
    {"date": "2025-02-17", "name": "Presidents' Day"},
    {"date": "2025-04-18", "name": "Good Friday"},
    {"date": "2025-05-26", "name": "Memorial Day"},
    {"date": "2025-06-19", "name": "Juneteenth"},
    {"date": "2025-07-04", "name": "Independence Day"},
    {"date": "2025-09-01", "name": "Labor Day"},
    {"date": "2025-11-27", "name": "Thanksgiving Day"},
    {"date": "2025-12-25", "name": "Christmas Day"},
    {"date": "2026-01-01", "name": "New Year's Day"},
    {"date": "2026-01-20", "name": "Martin Luther King Jr. Day"},
    {"date": "2026-02-16", "name": "Presidents' Day"},
    {"date": "2026-04-03", "name": "Good Friday"},
    {"date": "2026-05-25", "name": "Memorial Day"},
    {"date": "2026-06-19", "name": "Juneteenth"},
    {"date": "2026-07-03", "name": "Independence Day (observed)"},
    {"date": "2026-09-07", "name": "Labor Day"},
    {"date": "2026-11-26", "name": "Thanksgiving Day"},
    {"date": "2026-12-25", "name": "Christmas Day"}
  ]
}
```

## Testing Strategy

### Unit Tests Structure

```
tests/
├── utils/
│   └── test_time.py              # Test timezone utilities
├── market/
│   ├── test_hours.py            # Test market hours logic
│   └── test_holidays.py         # Test holiday management
└── tools/
    └── test_market_time_tool.py  # Test MCP tool integration
```

### Test Scenarios

1. **Timezone Tests**
   - Valid timezone conversions
   - Invalid timezone handling
   - DST transitions

2. **Market Hours Tests**
   - Pre-market detection (04:00-09:29 ET)
   - Market hours detection (09:30-15:59 ET)
   - After-hours detection (16:00-19:59 ET)
   - Closed hours detection
   - Weekend detection
   - Holiday detection

3. **Integration Tests**
   - MCP tool response format validation
   - Error handling and recovery
   - Performance under load

### Example Test Case

```python
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from src.market.hours import get_market_status, is_trading_day

class TestMarketHours:
    def test_market_open_time(self):
        """Test market status during regular trading hours."""
        # Create a datetime for a regular trading day at 10:00 AM ET
        test_time = datetime(2024, 11, 15, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(test_time) == "market"

    def test_weekend_closed(self):
        """Test that weekends are recognized as closed."""
        # Saturday
        saturday = datetime(2024, 11, 16, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(saturday) == "closed"
        assert not is_trading_day(saturday)

    def test_holiday_closed(self):
        """Test that holidays are recognized as closed."""
        # Christmas 2024
        christmas = datetime(2024, 12, 25, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(christmas) == "closed"
        assert not is_trading_day(christmas)
```

## Success Criteria

1. **Functionality**
   - Accurate US Eastern time retrieval
   - Correct market session identification
   - Proper trading day/holiday detection
   - Reliable next trading day calculation

2. **Performance**
   - Response time < 100ms for time status queries
   - Minimal memory footprint
   - Efficient holiday data caching

3. **Reliability**
   - Graceful handling of timezone errors
   - Proper error messages for debugging
   - No crashes on edge cases

4. **Integration**
   - Successful registration with MCP server
   - Proper JSON response format
   - Compatible with Claude Code client

## Future Extensions

This architecture is designed to easily accommodate future features:

### Near-term Extensions
1. **Market Events**
   - Fed announcement schedules
   - Earnings calendar integration
   - Economic data releases

2. **Multi-Market Support**
   - Add support for other exchanges (NASDAQ, NYSE, etc.)
   - International markets (LSE, TSE, HKEX)
   - Cryptocurrency markets (24/7 trading)

3. **Historical Data**
   - Past market status queries
   - Historical trading calendar
   - Market closure history

### Long-term Extensions
1. **Broker Integration** (`src/broker/`)
   - Interactive Brokers API
   - Schwab API
   - Alpaca API

2. **Data Providers** (`src/data_provider/`)
   - Yahoo Finance integration
   - Alpha Vantage API
   - Bloomberg Terminal integration

3. **Trading Strategies** (`src/strategy/`)
   - Momentum strategies
   - Mean reversion strategies
   - Options strategies

## Deployment Considerations

1. **Environment Variables**
   - `LOG_LEVEL`: Control logging verbosity
   - `DEBUG`: Enable debug mode
   - `PYTHONPATH`: Include project root

2. **Dependencies**
   - Python 3.13+ (for latest features)
   - FastMCP 2.0+ (MCP framework)
   - No external timezone libraries needed (uses built-in zoneinfo)

3. **Configuration File** (`.mcp.json`)
   ```json
   {
     "mcpServers": {
       "TradingAgentMCP": {
         "command": "uv",
         "args": ["run", "python", "/path/to/main.py"],
         "env": {
           "LOG_LEVEL": "INFO",
           "PYTHONPATH": "/path/to/project"
         }
       }
     }
   }
   ```

## Risk Mitigation

1. **Data Accuracy**
   - Regular updates to holiday calendars
   - Validation against official NYSE calendar
   - Automated tests for known edge cases

2. **Timezone Handling**
   - Use IANA timezone database
   - Handle DST transitions properly
   - Clear error messages for invalid timezones

3. **Performance**
   - Cache holiday data on first load
   - Minimize file I/O operations
   - Use efficient data structures

## Conclusion

This implementation plan provides a solid foundation for a Trading Agent MCP Server with market time functionality. The modular architecture ensures easy maintenance and extension, while the clear separation of concerns allows for parallel development of different components. The focus on configuration-driven design and English-language constants ensures international compatibility and ease of use.

The next steps after implementing this foundation would be to:
1. Add more sophisticated market analysis tools
2. Integrate with real-time market data feeds
3. Implement trading execution capabilities
4. Build portfolio management features

This design ensures that each new feature can be added without disrupting existing functionality, maintaining a stable and reliable trading infrastructure.
