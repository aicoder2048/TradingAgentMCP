"""
Stock history data retrieval and technical analysis module.

Provides comprehensive historical stock data retrieval, technical indicator 
calculation, and CSV file generation for the TradingAgent MCP Server.
"""

import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ..provider.tradier.client import TradierClient


def parse_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None, 
    date_range: Optional[str] = None
) -> Tuple[str, str]:
    """
    Parse various date formats and return standardized start and end dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        date_range: Relative date range like "30d", "3m", "1y" (optional)
    
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
        
    Raises:
        ValueError: For invalid date formats or logic
    """
    timezone = ZoneInfo("America/New_York")
    current_date = datetime.now(timezone)
    
    # Adjust current date to last trading day if weekend
    if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
        days_back = current_date.weekday() - 4  # Friday=4  
        current_date = current_date - timedelta(days=days_back)
    
    def parse_relative_range(range_str: str) -> timedelta:
        """Parse relative date ranges like '30d', '3m', '1y'."""
        if not range_str:
            return timedelta(days=90)  # default
            
        match = re.match(r'^(\d+)([dmy])$', range_str.lower())
        if not match:
            raise ValueError(f"Invalid date range format: {range_str}. Use format like '30d', '3m', '1y'")
            
        value, unit = int(match.group(1)), match.group(2)
        
        if unit == 'd':
            return timedelta(days=value)
        elif unit == 'm':
            return timedelta(days=value * 30)  # approximate months
        elif unit == 'y':
            return timedelta(days=value * 365)  # approximate years
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
    
    def parse_date(date_str: str) -> datetime:
        """Parse date string and validate format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone)
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format")
    
    # Priority 1: start_date + end_date (absolute range)
    if start_date and end_date:
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        
        if start_dt > end_dt:
            raise ValueError("Start date cannot be after end date")
        if end_dt > current_date:
            raise ValueError("End date cannot be in the future")
            
        return start_date, end_date
    
    # Priority 2: start_date + date_range (forward from start)
    elif start_date and date_range:
        start_dt = parse_date(start_date)
        range_delta = parse_relative_range(date_range)
        end_dt = start_dt + range_delta
        
        # Don't exceed current date
        if end_dt > current_date:
            end_dt = current_date
            
        return start_date, end_dt.strftime("%Y-%m-%d")
    
    # Priority 3: end_date + date_range (backward from end)
    elif end_date and date_range:
        end_dt = parse_date(end_date)
        range_delta = parse_relative_range(date_range)
        start_dt = end_dt - range_delta
        
        return start_dt.strftime("%Y-%m-%d"), end_date
        
    # Priority 4: date_range only (backward from current)
    elif date_range:
        range_delta = parse_relative_range(date_range)
        start_dt = current_date - range_delta
        
        return start_dt.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")
    
    # Priority 5: no parameters (default 90 days)
    else:
        start_dt = current_date - timedelta(days=90)
        return start_dt.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")


def generate_csv_filename(symbol: str, start_date: str, end_date: str) -> str:
    """
    Generate standardized CSV filename for stock history data.
    
    Args:
        symbol: Stock symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Filename in format: {SYMBOL}_{start_date}_{end_date}_{timestamp}.csv
    """
    timestamp = int(time.time())
    filename = f"{symbol.upper()}_{start_date}_{end_date}_{timestamp}.csv"
    return os.path.join("data", filename)


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comprehensive technical indicators for stock price data.
    
    Args:
        df: DataFrame with OHLCV columns (open, high, low, close, volume)
        
    Returns:
        DataFrame with additional technical indicator columns
    """
    try:
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Basic indicators
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Average True Range (ATR)
        df['prev_close'] = df['close'].shift(1)
        df['true_range'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['prev_close']),
                abs(df['low'] - df['prev_close'])
            )
        )
        df['atr_14'] = df['true_range'].rolling(window=14).mean()
        
        # Bollinger Bands
        bb_sma = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['upper_bollinger'] = bb_sma + (2 * bb_std)
        df['lower_bollinger'] = bb_sma - (2 * bb_std)
        
        # Historical Volatility (annualized)
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # RSI (Relative Strength Index)
        def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        df['rsi_14'] = calculate_rsi(df['close'], 14)
        
        # MACD (Moving Average Convergence Divergence)
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Clean up temporary columns
        df = df.drop(['prev_close', 'true_range', 'returns'], axis=1, errors='ignore')
        
        return df
        
    except Exception as e:
        # Return original dataframe if calculation fails
        print(f"Warning: Technical indicator calculation failed: {e}")
        return df


def save_to_csv(df: pd.DataFrame, filepath: str) -> str:
    """
    Save DataFrame to CSV file with proper formatting.
    
    Args:
        df: DataFrame to save
        filepath: Full filepath for the CSV file
        
    Returns:
        Full path of the saved file
        
    Raises:
        Exception: If file save fails
    """
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Format DataFrame for CSV output
        df_csv = df.copy()
        
        # Round numeric columns to reasonable precision
        numeric_columns = df_csv.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in ['volume']:
                df_csv[col] = df_csv[col].astype(int, errors='ignore')
            else:
                df_csv[col] = df_csv[col].round(4)
        
        # Save to CSV
        df_csv.to_csv(filepath, index=False)
        
        return filepath
        
    except Exception as e:
        raise Exception(f"Failed to save CSV file: {str(e)}")


async def get_stock_history_data(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "daily",
    include_indicators: bool = True,
    tradier_client: Optional[TradierClient] = None
) -> Dict[str, Any]:
    """
    Retrieve historical stock data from Tradier API and calculate technical indicators.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "TSLA")  
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval ("daily", "weekly", "monthly")
        include_indicators: Whether to calculate technical indicators
        tradier_client: Optional TradierClient instance
        
    Returns:
        Dictionary containing processed data, file path, and summary statistics
        
    Raises:
        Exception: For API errors, invalid symbols, or data processing issues
    """
    try:
        # Initialize Tradier client if not provided
        if not tradier_client:
            tradier_client = TradierClient()
        
        # Normalize symbol
        symbol = symbol.upper()
        
        # Map interval to Tradier API format
        interval_map = {
            "daily": "daily",
            "weekly": "weekly", 
            "monthly": "monthly"
        }
        api_interval = interval_map.get(interval, "daily")
        
        # Fetch historical data from Tradier API
        historical_data = tradier_client.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=api_interval
        )
        
        if not historical_data:
            raise Exception(f"No historical data found for {symbol}")
        
        # Convert to DataFrame
        df_data = []
        for data_point in historical_data:
            df_data.append({
                "date": data_point.date,
                "open": float(data_point.open),
                "high": float(data_point.high),
                "low": float(data_point.low),
                "close": float(data_point.close),
                "volume": int(data_point.volume)
            })
        
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        if df.empty:
            raise Exception(f"No valid data found for {symbol}")
        
        # Calculate technical indicators if requested
        if include_indicators:
            df = calculate_technical_indicators(df)
        
        # Generate CSV filename and save data
        csv_filename = generate_csv_filename(symbol, start_date, end_date)
        csv_path = save_to_csv(df, csv_filename)
        
        # Create summary statistics
        summary = create_summary_response(df, symbol, csv_path)
        
        return summary
        
    except Exception as e:
        raise Exception(f"Failed to get stock history data for {symbol}: {str(e)}")


def create_summary_response(df: pd.DataFrame, symbol: str, csv_path: str) -> Dict[str, Any]:
    """
    Create context-optimized summary response with key statistics and preview data.
    
    Args:
        df: DataFrame with historical data and indicators
        symbol: Stock symbol
        csv_path: Path to saved CSV file
        
    Returns:
        Dictionary with summary statistics and preview records
    """
    try:
        # Basic statistics
        total_records = len(df)
        first_date = df['date'].min().strftime("%Y-%m-%d")
        last_date = df['date'].max().strftime("%Y-%m-%d")
        
        # Price summary
        first_open = float(df['open'].iloc[0])
        last_close = float(df['close'].iloc[-1])
        max_high = float(df['high'].max())
        min_low = float(df['low'].min())
        total_return = last_close - first_open
        total_return_pct = (total_return / first_open) * 100 if first_open != 0 else 0
        
        # Volume summary
        avg_volume = int(df['volume'].mean())
        total_volume = int(df['volume'].sum())
        max_volume = int(df['volume'].max())
        min_volume = int(df['volume'].min())
        
        # Technical indicators (latest values)
        technical_indicators = {}
        if 'sma_20' in df.columns:
            latest_idx = -1
            technical_indicators.update({
                "current_sma_20": round(float(df['sma_20'].iloc[latest_idx]), 2) if not pd.isna(df['sma_20'].iloc[latest_idx]) else None,
                "current_ema_12": round(float(df['ema_12'].iloc[latest_idx]), 2) if not pd.isna(df['ema_12'].iloc[latest_idx]) else None,
                "current_ema_26": round(float(df['ema_26'].iloc[latest_idx]), 2) if not pd.isna(df['ema_26'].iloc[latest_idx]) else None,
                "current_atr_14": round(float(df['atr_14'].iloc[latest_idx]), 2) if not pd.isna(df['atr_14'].iloc[latest_idx]) else None,
                "current_rsi_14": round(float(df['rsi_14'].iloc[latest_idx]), 2) if not pd.isna(df['rsi_14'].iloc[latest_idx]) else None,
                "bollinger_upper": round(float(df['upper_bollinger'].iloc[latest_idx]), 2) if not pd.isna(df['upper_bollinger'].iloc[latest_idx]) else None,
                "bollinger_lower": round(float(df['lower_bollinger'].iloc[latest_idx]), 2) if not pd.isna(df['lower_bollinger'].iloc[latest_idx]) else None,
                "current_volatility": round(float(df['volatility'].iloc[latest_idx]), 4) if not pd.isna(df['volatility'].iloc[latest_idx]) else None,
                "macd": {
                    "macd_line": round(float(df['macd'].iloc[latest_idx]), 2) if not pd.isna(df['macd'].iloc[latest_idx]) else None,
                    "signal_line": round(float(df['macd_signal'].iloc[latest_idx]), 2) if not pd.isna(df['macd_signal'].iloc[latest_idx]) else None,
                    "histogram": round(float(df['macd_histogram'].iloc[latest_idx]), 2) if not pd.isna(df['macd_histogram'].iloc[latest_idx]) else None,
                }
            })
        
        # Preview records (last 30 records)
        preview_df = df.tail(30).copy()
        preview_records = []
        
        for _, row in preview_df.iterrows():
            record = {
                "date": row['date'].strftime("%Y-%m-%d"),
                "open": round(float(row['open']), 2),
                "high": round(float(row['high']), 2),
                "low": round(float(row['low']), 2),
                "close": round(float(row['close']), 2),
                "volume": int(row['volume'])
            }
            
            # Add technical indicators if available
            if 'sma_20' in row.index and not pd.isna(row['sma_20']):
                record['sma_20'] = round(float(row['sma_20']), 2)
            if 'ema_12' in row.index and not pd.isna(row['ema_12']):
                record['ema_12'] = round(float(row['ema_12']), 2)
            if 'ema_26' in row.index and not pd.isna(row['ema_26']):
                record['ema_26'] = round(float(row['ema_26']), 2)
            if 'atr_14' in row.index and not pd.isna(row['atr_14']):
                record['atr_14'] = round(float(row['atr_14']), 2)
            if 'rsi_14' in row.index and not pd.isna(row['rsi_14']):
                record['rsi_14'] = round(float(row['rsi_14']), 2)
            if 'upper_bollinger' in row.index and not pd.isna(row['upper_bollinger']):
                record['upper_bollinger'] = round(float(row['upper_bollinger']), 2)
            if 'lower_bollinger' in row.index and not pd.isna(row['lower_bollinger']):
                record['lower_bollinger'] = round(float(row['lower_bollinger']), 2)
            if 'volatility' in row.index and not pd.isna(row['volatility']):
                record['volatility'] = round(float(row['volatility']), 4)
            if 'macd' in row.index and not pd.isna(row['macd']):
                record['macd'] = round(float(row['macd']), 2)
            if 'macd_signal' in row.index and not pd.isna(row['macd_signal']):
                record['macd_signal'] = round(float(row['macd_signal']), 2)
            if 'macd_histogram' in row.index and not pd.isna(row['macd_histogram']):
                record['macd_histogram'] = round(float(row['macd_histogram']), 2)
                
            preview_records.append(record)
        
        # Build complete response
        response = {
            "status": "success",
            "symbol": symbol,
            "data_file": csv_path,
            "summary": {
                "total_records": total_records,
                "date_range": {
                    "start": first_date,
                    "end": last_date
                },
                "price_summary": {
                    "open_first": round(first_open, 2),
                    "close_last": round(last_close, 2),
                    "high_max": round(max_high, 2),
                    "low_min": round(min_low, 2),
                    "total_return": round(total_return, 2),
                    "total_return_pct": round(total_return_pct, 2)
                },
                "volume_summary": {
                    "average_volume": avg_volume,
                    "total_volume": total_volume,
                    "max_volume": max_volume,
                    "min_volume": min_volume
                },
                "technical_indicators": technical_indicators
            },
            "preview_records": preview_records
        }
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol,
            "error": f"Failed to create summary: {str(e)}"
        }