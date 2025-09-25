"""MCP tool for stock history data retrieval and technical analysis."""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.stock.history_data import (
    parse_date_range, 
    get_stock_history_data
)
from src.provider.tradier.client import TradierClient


async def get_stock_history_tool(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_range: Optional[str] = None,
    interval: str = "daily",
    include_indicators: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive stock history data with technical indicators and CSV export.
    
    This MCP tool retrieves historical stock price data and performs technical analysis:
    - Historical OHLCV data (Open, High, Low, Close, Volume)
    - Technical indicators (SMA, EMA, ATR, RSI, MACD, Bollinger Bands)
    - CSV file export for further analysis
    - Summary statistics and price performance metrics
    - Context-optimized preview (max 30 records)
    
    The data is sourced from real-time Tradier API and includes comprehensive
    technical analysis suitable for trading and investment research.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA", "NVDA")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)  
        date_range: Relative date range like "30d", "3m", "1y" (optional)
        interval: Data interval - "daily", "weekly", or "monthly" (default: "daily")
        include_indicators: Whether to calculate technical indicators (default: True)
    
    Date Range Examples:
        # Absolute dates
        start_date="2023-01-01", end_date="2023-12-31"
        
        # Relative ranges  
        date_range="30d"  # Last 30 days
        date_range="3m"   # Last 3 months
        date_range="1y"   # Last 1 year
        
        # Mixed modes
        start_date="2023-01-01", date_range="6m"  # 6 months from start date
        end_date="2023-12-31", date_range="3m"    # 3 months before end date
        
        # Default: Last 90 days if no date parameters provided
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - symbol: The requested stock symbol (normalized to uppercase)
        - data_file: Path to saved CSV file with complete dataset
        - summary: Comprehensive statistics including:
          - total_records: Number of data points retrieved
          - date_range: Actual start and end dates
          - price_summary: OHLC statistics and returns
          - volume_summary: Volume statistics and patterns
          - technical_indicators: Latest values of all calculated indicators
        - preview_records: Last 30 records with all data and indicators
        - timestamp: UTC timestamp of the response
        - error: Error message (only present if failed)
        
    Examples:
        # Get last 30 days of AAPL data
        >>> result = await get_stock_history_tool("AAPL", date_range="30d")
        >>> print(f"Data saved to: {result['data_file']}")
        Data saved to: data/AAPL_2023-11-01_2023-12-01_1701234567.csv
        >>> print(f"Total return: {result['summary']['price_summary']['total_return_pct']:.2f}%")
        Total return: 5.32%
        
        # Get specific date range with technical indicators
        >>> result = await get_stock_history_tool(
        ...     "TSLA", 
        ...     start_date="2023-01-01", 
        ...     end_date="2023-06-30",
        ...     include_indicators=True
        ... )
        >>> rsi = result['summary']['technical_indicators']['current_rsi_14']
        >>> print(f"Current RSI: {rsi}")
        Current RSI: 67.23
        
        # Get weekly data for broader analysis
        >>> result = await get_stock_history_tool(
        ...     "NVDA", 
        ...     date_range="1y", 
        ...     interval="weekly"
        ... )
        >>> print(f"Records: {result['summary']['total_records']}")
        Records: 52
    """
    try:
        # Normalize and validate symbol
        normalized_symbol = symbol.upper().strip()
        if not normalized_symbol:
            raise ValueError("Stock symbol cannot be empty")
            
        # Validate interval
        valid_intervals = ["daily", "weekly", "monthly"]
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval '{interval}'. Must be one of: {valid_intervals}")
        
        # Parse and validate date range
        try:
            parsed_start_date, parsed_end_date = parse_date_range(
                start_date=start_date,
                end_date=end_date,
                date_range=date_range
            )
        except ValueError as e:
            raise ValueError(f"Date parsing error: {str(e)}")
        
        # Initialize Tradier client
        tradier_client = TradierClient()
        
        # Get historical stock data
        history_data = await get_stock_history_data(
            symbol=normalized_symbol,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            interval=interval,
            include_indicators=include_indicators,
            tradier_client=tradier_client
        )
        
        # Generate response timestamp
        response_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Check if the request was successful
        if history_data.get("status") == "error":
            return {
                "status": "error",
                "symbol": normalized_symbol,
                "provider": "TRADIER",
                "error": history_data.get("error", "Unknown error occurred"),
                "timestamp": response_timestamp,
                "data_file": None,
                "summary": {},
                "preview_records": []
            }
        
        # Add metadata to successful response
        history_data.update({
            "provider": "TRADIER",
            "timestamp": response_timestamp,
            "request_params": {
                "symbol": normalized_symbol,
                "start_date": parsed_start_date,
                "end_date": parsed_end_date,
                "interval": interval,
                "include_indicators": include_indicators
            }
        })
        
        return history_data
        
    except ValueError as ve:
        # Handle validation errors with specific messages
        error_timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "status": "error",
            "symbol": symbol.upper().strip() if symbol else "UNKNOWN",
            "provider": "TRADIER",
            "error": f"Validation error: {str(ve)}",
            "timestamp": error_timestamp,
            "data_file": None,
            "summary": {},
            "preview_records": []
        }
        
    except Exception as e:
        # Handle any unexpected errors gracefully
        error_timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "status": "error", 
            "symbol": symbol.upper().strip() if symbol else "UNKNOWN",
            "provider": "TRADIER",
            "error": f"Failed to fetch stock history data for {symbol}",
            "details": str(e),
            "timestamp": error_timestamp,
            "data_file": None,
            "summary": {},
            "preview_records": []
        }