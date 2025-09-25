# Reference Implementation of Stock History Data Tool

```python
"""
Historical Data Retrieval Module
Provides tools to get historical price data and technical indicators
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from ..providers.tradier_client import TradierClient


async def get_historical_data(
    symbol: str,
    days,
    start_date: Optional[str],
    end_date: Optional[str],
    timeframe: str,
    provider: str,
    stock_client: Optional[StockHistoricalDataClient],
    tradier_client: Optional[TradierClient],
    include_records: bool = False,
    max_records=100,
) -> str:
    """
    Retrieve historical price data and calculate technical indicators

    Args:
        symbol: Stock symbol
        days: Number of days of historical data (ignored if start_date/end_date provided)
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional, defaults to last trading day)
        timeframe: Data timeframe (1Day, 1Hour, etc.)
        provider: Market data provider ('ALPACA' or 'TRADIER')
        stock_client: Alpaca stock data client (when using ALPACA)
        tradier_client: Tradier client (when using TRADIER)
        include_records: Include full historical data records in response
        max_records: Maximum number of records to return when including records

    Returns:
        JSON string with structured data including summary and optionally full records
    """
    try:
        # Ensure days parameter is an integer
        if isinstance(days, str):
            try:
                days = int(days)
            except (ValueError, TypeError):
                days = 90
        elif days is None:
            days = 90

        # Ensure max_records parameter is an integer
        if isinstance(max_records, str):
            try:
                max_records = int(max_records)
            except (ValueError, TypeError):
                max_records = 100
        elif max_records is None:
            max_records = 100

        if provider == "ALPACA":
            return await _get_historical_data_alpaca(
                symbol, days, start_date, end_date, timeframe, stock_client, include_records, max_records
            )
        elif provider == "TRADIER":
            return await _get_historical_data_tradier(
                symbol, days, start_date, end_date, timeframe, tradier_client, include_records, max_records
            )
        else:
            return json.dumps({"error": f"Unsupported provider: {provider}"}, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Error retrieving historical data for {symbol}: {str(e)}"}, indent=2)


def _calculate_date_range(
    days: int, start_date: Optional[str], end_date: Optional[str], timezone: ZoneInfo
) -> tuple[datetime, datetime]:
    """
    Calculate start and end dates for historical data retrieval

    Args:
        days: Number of days (used if start_date/end_date not provided)
        start_date: Start date string in YYYY-MM-DD format (optional)
        end_date: End date string in YYYY-MM-DD format (optional)
        timezone: Timezone to use for calculations

    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    if start_date and end_date:
        # Use provided date range
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone)
        # Set end date to end of day
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
    elif start_date:
        # Use start date and calculate end as today (or last trading day)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone)
        end_dt = datetime.now(timezone)
        # If today is weekend, use Friday
        if end_dt.weekday() >= 5:  # Saturday=5, Sunday=6
            days_back = end_dt.weekday() - 4  # Friday=4
            end_dt = end_dt - timedelta(days=days_back)
    elif end_date:
        # Use end date and calculate start based on days
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone)
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        start_dt = end_dt - timedelta(days=days)
    else:
        # Use default behavior: last N days ending at last trading day
        end_dt = datetime.now(timezone)
        # If today is weekend, use Friday
        if end_dt.weekday() >= 5:  # Saturday=5, Sunday=6
            days_back = end_dt.weekday() - 4  # Friday=4
            end_dt = end_dt - timedelta(days=days_back)
        start_dt = end_dt - timedelta(days=days)

    return start_dt, end_dt


async def _get_historical_data_alpaca(
    symbol: str,
    days: int,
    start_date: Optional[str],
    end_date: Optional[str],
    timeframe: str,
    stock_client: StockHistoricalDataClient,
    include_records: bool = False,
    max_records: int = 100,
) -> str:
    """Get historical data using Alpaca API"""
    timezone = ZoneInfo("America/New_York")

    # Calculate date range
    start_dt, end_dt = _calculate_date_range(days, start_date, end_date, timezone)

    # Parse timeframe
    if timeframe == "1Day":
        tf = TimeFrame(amount=1, unit=TimeFrameUnit.Day)
    elif timeframe == "1Hour":
        tf = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)
    elif timeframe == "15Min":
        tf = TimeFrame(amount=15, unit=TimeFrameUnit.Minute)
    else:
        tf = TimeFrame(amount=1, unit=TimeFrameUnit.Day)

    # Get historical data
    bars_request = StockBarsRequest(symbol_or_symbols=[symbol], timeframe=tf, start=start_dt, end=end_dt)

    bars_response = stock_client.get_stock_bars(bars_request)
    df = bars_response.df

    if df.empty:
        return f"No historical data found for {symbol}"

    # Reset index to work with timestamp as column
    df = df.reset_index()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Calculate technical indicators
    df = calculate_technical_indicators(df)

    # Create structured response with summary and optionally records
    result = _create_structured_response(df, symbol, "ALPACA", include_records, max_records)
    return json.dumps(result, indent=2)


async def _get_historical_data_tradier(
    symbol: str,
    days: int,
    start_date: Optional[str],
    end_date: Optional[str],
    timeframe: str,
    tradier_client: TradierClient,
    include_records: bool = False,
    max_records: int = 100,
) -> str:
    """Get historical data using Tradier API"""
    timezone = ZoneInfo("America/New_York")

    # Calculate date range
    start_dt, end_dt = _calculate_date_range(days, start_date, end_date, timezone)
    start_date_str = start_dt.strftime("%Y-%m-%d")
    end_date_str = end_dt.strftime("%Y-%m-%d")

    # Map timeframe to Tradier interval
    interval_map = {"1Day": "daily", "1Hour": "hourly", "15Min": "15min"}
    interval = interval_map.get(timeframe, "daily")

    # Get historical data
    historical_data = tradier_client.get_historical_data(
        symbol=symbol, start_date=start_date_str, end_date=end_date_str, interval=interval
    )

    if not historical_data:
        return f"No historical data found for {symbol}"

    # Convert to DataFrame
    df_data = []
    for data_point in historical_data:
        df_data.append(
            {
                "timestamp": pd.to_datetime(data_point.date),
                "open": data_point.open,
                "high": data_point.high,
                "low": data_point.low,
                "close": data_point.close,
                "volume": data_point.volume,
            }
        )

    df = pd.DataFrame(df_data)

    if df.empty:
        return f"No historical data found for {symbol}"

    # Calculate technical indicators
    df = calculate_technical_indicators(df)

    # Create structured response with summary and optionally records
    result = _create_structured_response(df, symbol, "TRADIER", include_records, max_records)
    return json.dumps(result, indent=2)


def _create_structured_response(
    df: pd.DataFrame, symbol: str, provider: str, include_records: bool = False, max_records: int = 100
) -> Dict[str, Any]:
    """
    Create structured response with summary and optionally raw data records

    Args:
        df: DataFrame with historical data and technical indicators
        symbol: Stock symbol
        provider: Data provider name
        include_records: Whether to include raw data records
        max_records: Maximum number of records to include

    Returns:
        Dictionary with structured response
    """
    # Basic summary stats
    current_price = df["close"].iloc[-1]
    price_change = current_price - df["close"].iloc[-2] if len(df) > 1 else 0
    price_change_pct = (price_change / df["close"].iloc[-2] * 100) if len(df) > 1 and df["close"].iloc[-2] != 0 else 0

    # Volume stats
    avg_volume = df["volume"].mean()
    latest_volume = df["volume"].iloc[-1]

    # Technical indicators (latest values, handling NaN)
    latest_sma_20 = df["sma_20"].iloc[-1] if not pd.isna(df["sma_20"].iloc[-1]) else None
    latest_atr_14 = df["atr_14"].iloc[-1] if not pd.isna(df["atr_14"].iloc[-1]) else None
    latest_volatility = df["volatility"].iloc[-1] if not pd.isna(df["volatility"].iloc[-1]) else None
    latest_upper_bollinger = df["upper_bollinger"].iloc[-1] if not pd.isna(df["upper_bollinger"].iloc[-1]) else None
    latest_lower_bollinger = df["lower_bollinger"].iloc[-1] if not pd.isna(df["lower_bollinger"].iloc[-1]) else None

    # Price ranges
    high_52w = df["high"].max()
    low_52w = df["low"].min()

    # Create summary
    summary = {
        "symbol": symbol,
        "provider": provider,
        "data_points": len(df),
        "date_range": {
            "start": df["timestamp"].min().strftime("%Y-%m-%d"),
            "end": df["timestamp"].max().strftime("%Y-%m-%d"),
        },
        "current_price": round(float(current_price), 2),
        "price_change": round(float(price_change), 2),
        "price_change_percent": round(float(price_change_pct), 2),
        "volume": {"latest": int(float(latest_volume)), "average": int(float(avg_volume))},
        "price_range": {"high": round(float(high_52w), 2), "low": round(float(low_52w), 2)},
        "technical_indicators": {
            "sma_20": round(latest_sma_20, 2) if latest_sma_20 is not None else None,
            "atr_14": round(latest_atr_14, 2) if latest_atr_14 is not None else None,
            "volatility": round(latest_volatility, 4) if latest_volatility is not None else None,
            "bollinger_bands": {
                "upper": round(latest_upper_bollinger, 2) if latest_upper_bollinger is not None else None,
                "lower": round(latest_lower_bollinger, 2) if latest_lower_bollinger is not None else None,
            },
        },
    }

    # Create base response
    response = {"status": "success", "summary": summary}

    # Add raw data records if requested
    if include_records:
        # Limit records to max_records (most recent)
        records_df = df.tail(max_records)

        # Convert DataFrame to list of dictionaries
        records = []
        for _, row in records_df.iterrows():
            record = {
                "date": row["timestamp"].strftime("%Y-%m-%d"),
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(float(row["volume"])),
            }

            # Add technical indicators if available (not NaN)
            if not pd.isna(row.get("sma_20")):
                record["sma_20"] = round(row["sma_20"], 2)
            if not pd.isna(row.get("atr_14")):
                record["atr_14"] = round(row["atr_14"], 2)
            if not pd.isna(row.get("volatility")):
                record["volatility"] = round(row["volatility"], 4)
            if not pd.isna(row.get("upper_bollinger")):
                record["upper_bollinger"] = round(row["upper_bollinger"], 2)
            if not pd.isna(row.get("lower_bollinger")):
                record["lower_bollinger"] = round(row["lower_bollinger"], 2)

            records.append(record)

        response["data"] = {
            "records": records,
            "record_count": len(records),
            "columns": list(records[0].keys()) if records else [],
        }

    return response


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators including SMA, ATR, Bollinger Bands, and volatility

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with additional technical indicator columns
    """
    try:
        # Simple Moving Average (20-period)
        df["sma_20"] = df["close"].rolling(window=20).mean()

        # Average True Range (14-period)
        df["prev_close"] = df["close"].shift(1)
        df["true_range"] = np.maximum(
            df["high"] - df["low"], np.maximum(abs(df["high"] - df["prev_close"]), abs(df["low"] - df["prev_close"]))
        )
        df["atr_14"] = df["true_range"].rolling(window=14).mean()

        # Bollinger Bands (20-period, 2 std dev)
        df["sma_20_bb"] = df["close"].rolling(window=20).mean()
        df["std_20"] = df["close"].rolling(window=20).std()
        df["upper_bollinger"] = df["sma_20_bb"] + (2 * df["std_20"])
        df["lower_bollinger"] = df["sma_20_bb"] - (2 * df["std_20"])

        # Historical Volatility (20-period annualized)
        df["returns"] = df["close"].pct_change()
        df["volatility"] = df["returns"].rolling(window=20).std() * np.sqrt(252)

        # Clean up temporary columns
        df = df.drop(["prev_close", "true_range", "sma_20_bb", "std_20", "returns"], axis=1)

        return df

    except Exception:
        # Return original dataframe if calculation fails
        return df

```
