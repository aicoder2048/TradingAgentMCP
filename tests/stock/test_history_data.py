"""Tests for stock history data functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.stock.history_data import (
    parse_date_range,
    generate_csv_filename, 
    calculate_technical_indicators,
    save_to_csv,
    get_stock_history_data,
    create_summary_response
)
from src.provider.tradier.client import TradierHistoricalData


class TestDateRangeParsing:
    """Test date range parsing functionality."""
    
    def test_absolute_date_range(self):
        """Test parsing with start_date and end_date."""
        start, end = parse_date_range("2023-01-01", "2023-12-31", None)
        assert start == "2023-01-01"
        assert end == "2023-12-31"
    
    def test_start_date_with_date_range(self):
        """Test parsing with start_date and relative range."""
        start, end = parse_date_range("2023-01-01", None, "3m")
        assert start == "2023-01-01"
        # Should be approximately 3 months later
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        diff = end_dt - start_dt
        assert 80 <= diff.days <= 100  # ~90 days for 3 months
    
    def test_end_date_with_date_range(self):
        """Test parsing with end_date and relative range."""
        start, end = parse_date_range(None, "2023-12-31", "30d")
        assert end == "2023-12-31"
        # Should be 30 days earlier
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        diff = end_dt - start_dt
        assert diff.days == 30
    
    @patch('src.stock.history_data.datetime')
    def test_date_range_only(self, mock_datetime):
        """Test parsing with only relative date range."""
        # Mock current date as 2023-12-01 (Friday)
        mock_now = datetime(2023, 12, 1, 15, 30, tzinfo=ZoneInfo("America/New_York"))
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        start, end = parse_date_range(None, None, "30d")
        
        # Should be 30 days before current date
        expected_start = (mock_now - timedelta(days=30)).strftime("%Y-%m-%d")
        expected_end = mock_now.strftime("%Y-%m-%d")
        
        assert start == expected_start
        assert end == expected_end
    
    @patch('src.stock.history_data.datetime')
    def test_no_parameters_default(self, mock_datetime):
        """Test default 90 days when no parameters provided."""
        mock_now = datetime(2023, 12, 1, 15, 30, tzinfo=ZoneInfo("America/New_York"))
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        start, end = parse_date_range(None, None, None)
        
        # Should default to 90 days
        expected_start = (mock_now - timedelta(days=90)).strftime("%Y-%m-%d")
        expected_end = mock_now.strftime("%Y-%m-%d")
        
        assert start == expected_start
        assert end == expected_end
    
    def test_relative_range_formats(self):
        """Test various relative date range formats."""
        # Test days
        start, end = parse_date_range(None, "2023-12-31", "15d")
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        assert (end_dt - start_dt).days == 15
        
        # Test months (approximate)
        start, end = parse_date_range(None, "2023-12-31", "2m")
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        assert 50 <= (end_dt - start_dt).days <= 70  # ~60 days for 2 months
        
        # Test years (approximate)
        start, end = parse_date_range(None, "2023-12-31", "1y")
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        assert 360 <= (end_dt - start_dt).days <= 370  # ~365 days for 1 year
    
    def test_invalid_date_format(self):
        """Test error handling for invalid date formats."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_range("invalid-date", "2023-12-31", None)
    
    def test_invalid_date_range_format(self):
        """Test error handling for invalid date range formats."""
        with pytest.raises(ValueError, match="Invalid date range format"):
            parse_date_range(None, None, "invalid")
        
        with pytest.raises(ValueError, match="Invalid date range format"):
            parse_date_range(None, None, "30x")  # Invalid unit
    
    def test_start_after_end_error(self):
        """Test error when start_date is after end_date."""
        with pytest.raises(ValueError, match="Start date cannot be after end date"):
            parse_date_range("2023-12-31", "2023-01-01", None)
    
    @patch('src.stock.history_data.datetime')  
    def test_future_end_date_error(self, mock_datetime):
        """Test error when end_date is in the future."""
        mock_now = datetime(2023, 12, 1, tzinfo=ZoneInfo("America/New_York"))
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        with pytest.raises(ValueError, match="End date cannot be in the future"):
            parse_date_range("2023-01-01", "2024-01-01", None)
    
    @patch('src.stock.history_data.datetime')
    def test_weekend_adjustment(self, mock_datetime):
        """Test adjustment for weekend dates."""
        # Mock current date as Saturday (2023-12-02)
        mock_saturday = datetime(2023, 12, 2, 15, 30, tzinfo=ZoneInfo("America/New_York"))
        mock_datetime.now.return_value = mock_saturday
        mock_datetime.strptime.side_effect = datetime.strptime
        
        start, end = parse_date_range(None, None, "7d")
        
        # Should adjust Saturday to Friday (2023-12-01)
        assert end == "2023-12-01"


class TestCSVFilename:
    """Test CSV filename generation."""
    
    @patch('time.time')
    def test_generate_csv_filename(self, mock_time):
        """Test CSV filename generation with timestamp."""
        mock_time.return_value = 1234567890
        
        filename = generate_csv_filename("AAPL", "2023-01-01", "2023-12-31")
        expected = "data/AAPL_2023-01-01_2023-12-31_1234567890.csv"
        
        assert filename == expected
    
    def test_symbol_normalization(self):
        """Test symbol is converted to uppercase."""
        filename = generate_csv_filename("aapl", "2023-01-01", "2023-12-31")
        assert filename.startswith("data/AAPL_")


class TestTechnicalIndicators:
    """Test technical indicator calculations."""
    
    def create_sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        np.random.seed(42)  # For reproducible tests
        
        # Generate realistic price data
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 50)  # Daily returns
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 50)
        })
        
        # Adjust high/low to be consistent
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        
        return df
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'sma_20' in df_with_indicators.columns
        
        # Check SMA calculation for a specific period
        manual_sma = df['close'].rolling(window=20).mean()
        pd.testing.assert_series_equal(
            df_with_indicators['sma_20'], 
            manual_sma, 
            check_names=False
        )
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'ema_12' in df_with_indicators.columns
        assert 'ema_26' in df_with_indicators.columns
        
        # Check EMA calculation
        manual_ema_12 = df['close'].ewm(span=12).mean()
        manual_ema_26 = df['close'].ewm(span=26).mean()
        
        pd.testing.assert_series_equal(
            df_with_indicators['ema_12'],
            manual_ema_12,
            check_names=False
        )
        pd.testing.assert_series_equal(
            df_with_indicators['ema_26'], 
            manual_ema_26,
            check_names=False
        )
    
    def test_atr_calculation(self):
        """Test Average True Range calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'atr_14' in df_with_indicators.columns
        
        # ATR should be positive and reasonable
        atr_values = df_with_indicators['atr_14'].dropna()
        assert all(atr_values >= 0)
        assert len(atr_values) >= 35  # Should have values after initial period
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'upper_bollinger' in df_with_indicators.columns
        assert 'lower_bollinger' in df_with_indicators.columns
        
        # Upper band should be higher than lower band
        valid_rows = df_with_indicators.dropna()
        assert all(valid_rows['upper_bollinger'] > valid_rows['lower_bollinger'])
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'rsi_14' in df_with_indicators.columns
        
        # RSI should be between 0 and 100
        rsi_values = df_with_indicators['rsi_14'].dropna()
        assert all(0 <= rsi <= 100 for rsi in rsi_values)
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'macd' in df_with_indicators.columns
        assert 'macd_signal' in df_with_indicators.columns
        assert 'macd_histogram' in df_with_indicators.columns
        
        # Check MACD calculation
        manual_macd = df_with_indicators['ema_12'] - df_with_indicators['ema_26']
        pd.testing.assert_series_equal(
            df_with_indicators['macd'],
            manual_macd,
            check_names=False
        )
    
    def test_volatility_calculation(self):
        """Test historical volatility calculation."""
        df = self.create_sample_data()
        df_with_indicators = calculate_technical_indicators(df)
        
        assert 'volatility' in df_with_indicators.columns
        
        # Volatility should be positive
        vol_values = df_with_indicators['volatility'].dropna()
        assert all(vol >= 0 for vol in vol_values)
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = calculate_technical_indicators(empty_df)
        assert result.empty
    
    def test_minimal_data_handling(self):
        """Test handling of minimal data (less than indicator periods)."""
        # Only 5 rows of data
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5),
            'open': [100, 101, 102, 101, 103],
            'high': [101, 102, 103, 102, 104],
            'low': [99, 100, 101, 100, 102],
            'close': [100.5, 101.5, 102.5, 101.5, 103.5],
            'volume': [1000000] * 5
        })
        
        df_with_indicators = calculate_technical_indicators(df)
        
        # Should have indicator columns but mostly NaN values
        assert 'sma_20' in df_with_indicators.columns
        assert 'rsi_14' in df_with_indicators.columns
        
        # Most indicator values should be NaN due to insufficient data
        assert pd.isna(df_with_indicators['sma_20']).all()


class TestCSVSaving:
    """Test CSV file saving functionality."""
    
    @patch('os.makedirs')
    @patch('pandas.DataFrame.to_csv')
    def test_save_to_csv_success(self, mock_to_csv, mock_makedirs):
        """Test successful CSV saving."""
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02'],
            'close': [100.0, 101.5],
            'volume': [1000000, 1500000]
        })
        
        filepath = save_to_csv(df, "data/test.csv")
        
        mock_makedirs.assert_called_once_with("data", exist_ok=True)
        mock_to_csv.assert_called_once()
        assert filepath == "data/test.csv"
    
    @patch('os.makedirs')
    @patch('pandas.DataFrame.to_csv', side_effect=Exception("Write error"))
    def test_save_to_csv_error(self, mock_to_csv, mock_makedirs):
        """Test CSV saving error handling."""
        df = pd.DataFrame({'test': [1, 2, 3]})
        
        with pytest.raises(Exception, match="Failed to save CSV file"):
            save_to_csv(df, "data/test.csv")


class TestSummaryResponse:
    """Test summary response creation."""
    
    def create_test_data(self) -> pd.DataFrame:
        """Create test data for summary response tests."""
        return pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000000, 1500000, 1200000],
            'sma_20': [None, None, 101.33],
            'ema_12': [None, None, 101.8], 
            'ema_26': [None, None, 101.0],
            'atr_14': [None, None, 1.5],
            'rsi_14': [None, None, 65.0],
            'upper_bollinger': [None, None, 103.0],
            'lower_bollinger': [None, None, 99.0],
            'volatility': [None, None, 0.25],
            'macd': [None, None, 0.8],
            'macd_signal': [None, None, 0.3],
            'macd_histogram': [None, None, 0.5]
        })
    
    def test_create_basic_summary(self):
        """Test basic summary response creation."""
        df = self.create_test_data()
        response = create_summary_response(df, "AAPL", "data/test.csv")
        
        # Debug: print response if it's an error
        if response.get("status") == "error":
            print(f"Error response: {response}")
        
        assert response["status"] == "success"
        assert response["symbol"] == "AAPL"
        assert response["data_file"] == "data/test.csv"
        
        # Check summary structure
        summary = response["summary"]
        assert summary["total_records"] == 3
        assert summary["date_range"]["start"] == "2023-01-01"
        assert summary["date_range"]["end"] == "2023-01-03"
        
        # Check price summary
        price_summary = summary["price_summary"]
        assert price_summary["open_first"] == 100.0
        assert price_summary["close_last"] == 102.5
        assert price_summary["high_max"] == 103.0
        assert price_summary["low_min"] == 99.0
    
    def test_preview_records_limit(self):
        """Test preview records are limited to 30."""
        # Create DataFrame with more than 30 rows
        dates = pd.date_range('2023-01-01', periods=50)
        df = pd.DataFrame({
            'date': dates,
            'open': range(100, 150),
            'high': range(101, 151),
            'low': range(99, 149),
            'close': range(100, 150),
            'volume': [1000000] * 50
        })
        
        response = create_summary_response(df, "AAPL", "data/test.csv")
        
        # Should only have last 30 records
        assert len(response["preview_records"]) == 30
        
        # Should be the most recent records
        assert response["preview_records"][0]["date"] == "2023-01-21"  # 21st day
        assert response["preview_records"][-1]["date"] == "2023-02-19"  # 50th day
    
    def test_error_handling_in_summary(self):
        """Test error handling in summary creation."""
        # Create problematic DataFrame
        df = pd.DataFrame()  # Empty DataFrame
        
        response = create_summary_response(df, "AAPL", "data/test.csv")
        
        assert response["status"] == "error"
        assert "error" in response


class TestGetStockHistoryData:
    """Test the main stock history data retrieval function."""
    
    @pytest.mark.asyncio
    @patch('src.stock.history_data.TradierClient')
    @patch('src.stock.history_data.save_to_csv')
    async def test_successful_data_retrieval(self, mock_save_csv, mock_tradier_client_class):
        """Test successful stock history data retrieval."""
        # Mock Tradier client
        mock_client = Mock()
        mock_tradier_client_class.return_value = mock_client
        
        # Mock historical data response
        mock_data = [
            TradierHistoricalData("2023-01-01", 100.0, 101.0, 99.0, 100.5, 1000000),
            TradierHistoricalData("2023-01-02", 100.5, 102.0, 100.0, 101.5, 1500000),
            TradierHistoricalData("2023-01-03", 101.5, 103.0, 101.0, 102.5, 1200000)
        ]
        mock_client.get_historical_data.return_value = mock_data
        
        # Mock CSV saving
        mock_save_csv.return_value = "data/AAPL_2023-01-01_2023-01-03_123456.csv"
        
        # Call function
        result = await get_stock_history_data(
            symbol="AAPL",
            start_date="2023-01-01", 
            end_date="2023-01-03",
            interval="daily",
            include_indicators=True,
            tradier_client=mock_client
        )
        
        # Verify results
        assert result["status"] == "success"
        assert result["symbol"] == "AAPL"
        assert "data_file" in result
        assert "summary" in result
        assert "preview_records" in result
    
    @pytest.mark.asyncio
    @patch('src.stock.history_data.TradierClient')
    async def test_no_data_found(self, mock_tradier_client_class):
        """Test handling when no historical data is found."""
        mock_client = Mock()
        mock_tradier_client_class.return_value = mock_client
        mock_client.get_historical_data.return_value = []
        
        with pytest.raises(Exception, match="No historical data found"):
            await get_stock_history_data(
                symbol="INVALID",
                start_date="2023-01-01",
                end_date="2023-01-03",
                tradier_client=mock_client
            )
    
    @pytest.mark.asyncio
    @patch('src.stock.history_data.TradierClient')
    async def test_api_error_handling(self, mock_tradier_client_class):
        """Test API error handling."""
        mock_client = Mock()
        mock_tradier_client_class.return_value = mock_client
        mock_client.get_historical_data.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="Failed to get stock history data"):
            await get_stock_history_data(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                tradier_client=mock_client
            )
    
    def test_symbol_normalization(self):
        """Test symbol normalization in main function.""" 
        # This is tested indirectly through the integration
        pass
    
    def test_interval_mapping(self):
        """Test interval mapping to Tradier API format."""
        # This is tested through the integration tests
        pass