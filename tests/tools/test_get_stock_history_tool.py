"""Integration tests for the stock history MCP tool."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import pandas as pd

from src.mcp_server.tools.get_stock_history_tool import get_stock_history_tool
from src.provider.tradier.client import TradierHistoricalData


@pytest.mark.asyncio
class TestGetStockHistoryTool:
    """Integration tests for the stock history MCP tool."""

    @patch('src.mcp_server.tools.get_stock_history_tool.TradierClient')
    @patch('src.stock.history_data.save_to_csv')
    async def test_successful_tool_call(self, mock_save_csv, mock_tradier_client_class):
        """Test successful stock history tool execution."""
        # Mock Tradier client
        mock_client = Mock()
        mock_tradier_client_class.return_value = mock_client
        
        # Mock historical data response
        mock_data = [
            TradierHistoricalData("2023-01-01", 100.0, 101.0, 99.0, 100.5, 1000000),
            TradierHistoricalData("2023-01-02", 100.5, 102.0, 100.0, 101.5, 1500000),
            TradierHistoricalData("2023-01-03", 101.5, 103.0, 101.0, 102.5, 1200000),
            TradierHistoricalData("2023-01-04", 102.5, 104.0, 102.0, 103.0, 1800000),
            TradierHistoricalData("2023-01-05", 103.0, 105.0, 102.5, 104.0, 2000000)
        ]
        mock_client.get_historical_data.return_value = mock_data
        
        # Mock CSV saving
        mock_save_csv.return_value = "data/AAPL_2023-01-01_2023-01-05_123456.csv"
        
        # Call the tool
        result = await get_stock_history_tool(
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-05",
            interval="daily",
            include_indicators=True
        )
        
        # Verify response structure
        assert result["status"] == "success"
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert "timestamp" in result
        assert "request_params" in result
        
        # Verify data file
        assert result["data_file"] == "data/AAPL_2023-01-01_2023-01-05_123456.csv"
        
        # Verify summary structure
        summary = result["summary"]
        assert summary["total_records"] == 5
        assert summary["date_range"]["start"] == "2023-01-01"
        assert summary["date_range"]["end"] == "2023-01-05"
        
        # Verify price summary
        price_summary = summary["price_summary"]
        assert price_summary["open_first"] == 100.0
        assert price_summary["close_last"] == 104.0
        assert price_summary["high_max"] == 105.0
        assert price_summary["low_min"] == 99.0
        assert price_summary["total_return"] == 4.0  # 104.0 - 100.0
        assert price_summary["total_return_pct"] == 4.0  # 4%
        
        # Verify volume summary
        volume_summary = summary["volume_summary"]
        assert volume_summary["average_volume"] == 1500000
        assert volume_summary["total_volume"] == 7500000
        assert volume_summary["max_volume"] == 2000000
        assert volume_summary["min_volume"] == 1000000
        
        # Verify technical indicators present
        assert "technical_indicators" in summary
        
        # Verify preview records
        assert "preview_records" in result
        assert len(result["preview_records"]) == 5  # All 5 records since less than 30
        
        # Verify request parameters
        request_params = result["request_params"]
        assert request_params["symbol"] == "AAPL"
        assert request_params["start_date"] == "2023-01-01"
        assert request_params["end_date"] == "2023-01-05"
        assert request_params["interval"] == "daily"
        assert request_params["include_indicators"] is True

    async def test_symbol_normalization(self):
        """Test that symbol is normalized to uppercase."""
        with patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data') as mock_get_data:
            mock_get_data.return_value = {
                "status": "success",
                "symbol": "AAPL",
                "data_file": "test.csv",
                "summary": {},
                "preview_records": []
            }
            
            result = await get_stock_history_tool(
                symbol="aapl",  # lowercase
                date_range="30d"
            )
            
            # Should be normalized to uppercase
            mock_get_data.assert_called_once()
            call_args = mock_get_data.call_args[1]
            assert call_args["symbol"] == "AAPL"

    async def test_empty_symbol_validation(self):
        """Test validation of empty symbol."""
        result = await get_stock_history_tool(
            symbol="",
            date_range="30d"
        )
        
        assert result["status"] == "error"
        assert "Stock symbol cannot be empty" in result["error"]
        assert result["data_file"] is None

    async def test_invalid_interval_validation(self):
        """Test validation of invalid interval."""
        result = await get_stock_history_tool(
            symbol="AAPL",
            date_range="30d",
            interval="invalid"
        )
        
        assert result["status"] == "error"
        assert "Invalid interval" in result["error"]
        assert result["data_file"] is None

    async def test_invalid_date_format_validation(self):
        """Test validation of invalid date formats."""
        result = await get_stock_history_tool(
            symbol="AAPL",
            start_date="invalid-date",
            end_date="2023-12-31"
        )
        
        assert result["status"] == "error"
        assert "Date parsing error" in result["error"]
        assert result["data_file"] is None

    @patch('src.mcp_server.tools.get_stock_history_tool.parse_date_range')
    async def test_date_parsing_integration(self, mock_parse_date_range):
        """Test integration with date parsing logic."""
        mock_parse_date_range.return_value = ("2023-01-01", "2023-01-31")
        
        with patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data') as mock_get_data:
            mock_get_data.return_value = {
                "status": "success",
                "symbol": "AAPL", 
                "data_file": "test.csv",
                "summary": {},
                "preview_records": []
            }
            
            await get_stock_history_tool(
                symbol="AAPL",
                date_range="1m"
            )
            
            # Verify date parsing was called
            mock_parse_date_range.assert_called_once_with(
                start_date=None,
                end_date=None,
                date_range="1m"
            )
            
            # Verify parsed dates were used
            mock_get_data.assert_called_once()
            call_args = mock_get_data.call_args[1]
            assert call_args["start_date"] == "2023-01-01"
            assert call_args["end_date"] == "2023-01-31"

    async def test_different_intervals(self):
        """Test different data intervals."""
        intervals = ["daily", "weekly", "monthly"]
        
        for interval in intervals:
            with patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data') as mock_get_data:
                mock_get_data.return_value = {
                    "status": "success",
                    "symbol": "AAPL",
                    "data_file": "test.csv",
                    "summary": {},
                    "preview_records": []
                }
                
                await get_stock_history_tool(
                    symbol="AAPL",
                    date_range="30d",
                    interval=interval
                )
                
                # Verify interval was passed correctly
                call_args = mock_get_data.call_args[1]
                assert call_args["interval"] == interval

    async def test_include_indicators_flag(self):
        """Test include_indicators parameter."""
        for include_indicators in [True, False]:
            with patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data') as mock_get_data:
                mock_get_data.return_value = {
                    "status": "success",
                    "symbol": "AAPL",
                    "data_file": "test.csv", 
                    "summary": {},
                    "preview_records": []
                }
                
                await get_stock_history_tool(
                    symbol="AAPL",
                    date_range="30d",
                    include_indicators=include_indicators
                )
                
                # Verify flag was passed correctly
                call_args = mock_get_data.call_args[1]
                assert call_args["include_indicators"] == include_indicators

    @patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data')
    async def test_core_module_error_handling(self, mock_get_data):
        """Test handling of errors from core module."""
        mock_get_data.return_value = {
            "status": "error",
            "error": "Core module error",
            "symbol": "AAPL"
        }
        
        result = await get_stock_history_tool(
            symbol="AAPL",
            date_range="30d"
        )
        
        assert result["status"] == "error"
        assert result["error"] == "Core module error"
        assert result["data_file"] is None
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert "timestamp" in result

    @patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data')
    async def test_unexpected_exception_handling(self, mock_get_data):
        """Test handling of unexpected exceptions."""
        mock_get_data.side_effect = Exception("Unexpected error")
        
        result = await get_stock_history_tool(
            symbol="AAPL",
            date_range="30d"
        )
        
        assert result["status"] == "error"
        assert "Failed to fetch stock history data" in result["error"]
        assert "Unexpected error" in result["details"]
        assert result["data_file"] is None
        assert result["symbol"] == "AAPL"
        assert "timestamp" in result

    async def test_response_metadata(self):
        """Test response includes proper metadata."""
        with patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data') as mock_get_data:
            mock_get_data.return_value = {
                "status": "success",
                "symbol": "AAPL",
                "data_file": "test.csv",
                "summary": {},
                "preview_records": []
            }
            
            result = await get_stock_history_tool(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-31",
                interval="daily",
                include_indicators=True
            )
            
            # Check metadata
            assert result["provider"] == "TRADIER"
            assert "timestamp" in result
            
            # Verify timestamp format (ISO format)
            timestamp = result["timestamp"]
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise
            
            # Check request parameters are saved
            request_params = result["request_params"]
            assert request_params["symbol"] == "AAPL"
            assert request_params["start_date"] == "2023-01-01"
            assert request_params["end_date"] == "2023-01-31"
            assert request_params["interval"] == "daily"
            assert request_params["include_indicators"] is True

    @patch('src.mcp_server.tools.get_stock_history_tool.TradierClient')
    @patch('src.stock.history_data.save_to_csv')
    async def test_default_parameters(self, mock_save_csv, mock_tradier_client_class):
        """Test tool with default parameters."""
        # Mock Tradier client  
        mock_client = Mock()
        mock_tradier_client_class.return_value = mock_client
        
        # Mock minimal historical data
        mock_data = [
            TradierHistoricalData("2023-12-01", 100.0, 101.0, 99.0, 100.5, 1000000)
        ]
        mock_client.get_historical_data.return_value = mock_data
        mock_save_csv.return_value = "data/AAPL_test.csv"
        
        # Call with minimal parameters
        result = await get_stock_history_tool(symbol="AAPL")
        
        assert result["status"] == "success"
        assert result["symbol"] == "AAPL"
        
        # Check that defaults were applied
        request_params = result["request_params"]
        assert request_params["interval"] == "daily"
        assert request_params["include_indicators"] is True
        assert request_params["start_date"] is not None  # Should have parsed default
        assert request_params["end_date"] is not None

    async def test_date_range_combinations(self):
        """Test various date range parameter combinations."""
        test_cases = [
            # (start_date, end_date, date_range)
            ("2023-01-01", "2023-12-31", None),  # Absolute range
            ("2023-01-01", None, "6m"),          # Start + range
            (None, "2023-12-31", "3m"),          # End + range  
            (None, None, "30d"),                 # Range only
            (None, None, None)                   # Default
        ]
        
        for start_date, end_date, date_range in test_cases:
            with patch('src.mcp_server.tools.get_stock_history_tool.get_stock_history_data') as mock_get_data:
                mock_get_data.return_value = {
                    "status": "success",
                    "symbol": "AAPL",
                    "data_file": "test.csv",
                    "summary": {},
                    "preview_records": []
                }
                
                result = await get_stock_history_tool(
                    symbol="AAPL",
                    start_date=start_date,
                    end_date=end_date,
                    date_range=date_range
                )
                
                assert result["status"] == "success"
                
                # Verify parameters were stored
                request_params = result["request_params"]
                assert request_params["start_date"] is not None
                assert request_params["end_date"] is not None