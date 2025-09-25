"""Tests for stock info MCP tool."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timezone
from src.mcp_server.tools.stock_key_info_tool import get_stock_key_info
from src.stock.info import StockInfo


class TestStockInfoTool:
    """Test suite for get_stock_key_info MCP tool."""

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_get_stock_key_info_success(self, mock_processor_class):
        """Test successful stock info retrieval."""
        # Setup mock processor
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        
        # Create mock stock info
        mock_stock_info = StockInfo(
            symbol="TSLA",
            company_name="Tesla Inc",
            close_price=442.79,
            close_time="09/25 16:00:00 (美东收盘)",
            change_amount=16.94,
            change_percentage=3.98,
            high_price=444.21,
            low_price=429.03,
            open_price=429.83,
            prev_close=425.85,
            volume=93133600,
            market_status="closed"
        )
        
        # Setup mock responses
        mock_processor.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_processor.format_stock_info = Mock(return_value="## TSLA (Tesla Inc) - 关键信息\n\n**基础信息**\n- 股票代码: TSLA")
        mock_processor.get_raw_data_dict = Mock(return_value={
            "symbol": "TSLA",
            "price_data": {"close_price": 442.79}
        })
        
        # Execute
        result = await get_stock_key_info("tsla")  # Test case conversion
        
        # Verify response structure
        assert result["success"] is True
        assert result["symbol"] == "TSLA"
        assert "formatted_info" in result
        assert "raw_data" in result
        assert "timestamp" in result
        assert "error" not in result
        
        # Verify content
        assert "TSLA (Tesla Inc)" in result["formatted_info"]
        assert result["raw_data"]["symbol"] == "TSLA"
        assert result["raw_data"]["price_data"]["close_price"] == 442.79
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        assert timestamp.tzinfo is not None
        
        # Verify processor was called correctly
        mock_processor.get_stock_info.assert_called_once_with("TSLA")
        mock_processor.format_stock_info.assert_called_once_with(mock_stock_info)
        mock_processor.get_raw_data_dict.assert_called_once_with(mock_stock_info)

    @pytest.mark.asyncio 
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_get_stock_key_info_with_comprehensive_data(self, mock_processor_class):
        """Test stock info retrieval with comprehensive data."""
        # Setup mock processor
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        
        # Create comprehensive mock stock info
        mock_stock_info = StockInfo(
            symbol="TSLA",
            company_name="特斯拉",
            close_price=442.79,
            close_time="09/25 16:00:00 (美东收盘)",
            change_amount=16.94,
            change_percentage=3.98,
            high_price=444.21,
            low_price=429.03,
            open_price=429.83,
            prev_close=425.85,
            volume=93133600,
            turnover_amount=4.08e10,
            pe_ratio_ttm=263.57,
            pb_ratio=19.04,
            market_cap=1.47e12,
            beta=2.334,
            premarket_price=440.68,
            premarket_change=-2.11,
            premarket_change_percentage=-0.48,
            market_status="closed"
        )
        
        # Setup comprehensive formatted response
        formatted_response = """## TSLA (特斯拉) - 关键信息

**基础信息**
- 股票代码: TSLA
- 收盘价: $442.790
- 收盘时间: 09/25 16:00:00 (美东收盘)

**价格变动**
- 涨跌额: +16.940
- 涨跌幅: +3.98%

**估值指标**
- 市盈率TTM: 263.57
- 市净率: 19.04

**盘前交易**
- 盘前价格: $440.680
- 盘前变动: $-2.110 (-0.48%)"""
        
        # Setup comprehensive raw data
        raw_data_response = {
            "symbol": "TSLA",
            "company_name": "特斯拉",
            "price_data": {
                "close_price": 442.79,
                "change_amount": 16.94,
                "change_percentage": 3.98
            },
            "valuation_metrics": {
                "pe_ratio_ttm": 263.57,
                "pb_ratio": 19.04,
                "market_cap": 1.47e12
            },
            "premarket_data": {
                "premarket_price": 440.68,
                "premarket_change": -2.11,
                "premarket_change_percentage": -0.48
            },
            "context": {
                "market_status": "closed"
            }
        }
        
        # Setup mock responses
        mock_processor.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_processor.format_stock_info = Mock(return_value=formatted_response)
        mock_processor.get_raw_data_dict = Mock(return_value=raw_data_response)
        
        # Execute
        result = await get_stock_key_info("TSLA")
        
        # Verify comprehensive data
        assert result["success"] is True
        assert result["symbol"] == "TSLA"
        
        # Verify formatted info contains key sections
        formatted = result["formatted_info"]
        assert "基础信息" in formatted
        assert "价格变动" in formatted
        assert "估值指标" in formatted
        assert "盘前交易" in formatted
        assert "市盈率TTM: 263.57" in formatted
        
        # Verify raw data structure
        raw_data = result["raw_data"]
        assert raw_data["price_data"]["close_price"] == 442.79
        assert raw_data["valuation_metrics"]["market_cap"] == 1.47e12
        assert raw_data["premarket_data"]["premarket_price"] == 440.68
        assert raw_data["context"]["market_status"] == "closed"

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_get_stock_key_info_processor_error(self, mock_processor_class):
        """Test handling of processor errors."""
        # Setup mock processor to raise exception
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.get_stock_info.side_effect = Exception("API Error: Invalid symbol")
        
        # Execute
        result = await get_stock_key_info("INVALID")
        
        # Verify error response
        assert result["success"] is False
        assert result["symbol"] == "INVALID"
        assert "error" in result
        assert "API Error: Invalid symbol" in result["error"]
        assert "timestamp" in result
        assert result["raw_data"] is None
        
        # Verify formatted error message
        assert "❌ 无法获取 INVALID 的股票信息" in result["formatted_info"]
        assert "错误: API Error: Invalid symbol" in result["formatted_info"]
        
        # Verify processor was called
        mock_processor.get_stock_info.assert_called_once_with("INVALID")

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_get_stock_key_info_format_error(self, mock_processor_class):
        """Test handling of formatting errors."""
        # Setup mock processor
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        
        mock_stock_info = Mock()
        mock_stock_info.symbol = "TSLA"
        
        # Make get_stock_info succeed but format_stock_info fail
        mock_processor.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_processor.format_stock_info = Mock(side_effect=Exception("Formatting error"))
        
        # Execute
        result = await get_stock_key_info("TSLA")
        
        # Verify error handling
        assert result["success"] is False
        assert result["symbol"] == "TSLA"
        assert "Formatting error" in result["error"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_get_stock_key_info_initialization_error(self, mock_processor_class):
        """Test handling of processor initialization errors."""
        # Make processor initialization fail
        mock_processor_class.side_effect = Exception("Failed to initialize Tradier client")
        
        # Execute
        result = await get_stock_key_info("TSLA")
        
        # Verify error handling
        assert result["success"] is False
        assert result["symbol"] == "TSLA"
        assert "Failed to initialize Tradier client" in result["error"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_symbol_normalization(self, mock_processor_class):
        """Test that symbols are properly normalized to uppercase."""
        # Setup mock processor
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        
        mock_stock_info = Mock()
        mock_stock_info.symbol = "AAPL"
        
        mock_processor.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_processor.format_stock_info = Mock(return_value="Mock format")
        mock_processor.get_raw_data_dict = Mock(return_value={"symbol": "AAPL"})
        
        # Test various case inputs
        test_cases = ["aapl", "Aapl", "AAPL", "aApL"]
        
        for input_symbol in test_cases:
            # Execute
            result = await get_stock_key_info(input_symbol)
            
            # Verify symbol normalization
            assert result["symbol"] == "AAPL"
            mock_processor.get_stock_info.assert_called_with("AAPL")

    @pytest.mark.asyncio
    async def test_timestamp_format(self):
        """Test that timestamps are in correct ISO format with timezone."""
        with patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor_class.return_value = mock_processor
            mock_processor.get_stock_info.side_effect = Exception("Test error")
            
            # Execute (will hit error path which also generates timestamp)
            result = await get_stock_key_info("TEST")
            
            # Verify timestamp format
            timestamp_str = result["timestamp"]
            
            # Should be ISO format with timezone info
            assert timestamp_str.endswith("Z") or "+" in timestamp_str or timestamp_str.endswith(":00")
            
            # Should be parseable as datetime
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            
            parsed_time = datetime.fromisoformat(timestamp_str)
            assert parsed_time.tzinfo is not None

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.stock_key_info_tool.StockInfoProcessor')
    async def test_empty_symbol_handling(self, mock_processor_class):
        """Test handling of empty or whitespace symbols."""
        # Setup mock processor
        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.get_stock_info.side_effect = Exception("No data found for symbol: ")
        
        # Test empty and whitespace symbols
        test_cases = ["", "   ", "\t", "\n"]
        
        for empty_symbol in test_cases:
            result = await get_stock_key_info(empty_symbol)
            
            # Should handle gracefully
            assert result["success"] is False
            assert "error" in result


class TestStockInfoToolIntegration:
    """Integration tests for stock info tool."""

    @pytest.mark.asyncio
    @patch('src.stock.info.TradierClient')
    @patch('src.stock.info.get_timezone_time')
    @patch('src.stock.info.get_market_status')
    async def test_end_to_end_success_scenario(
        self, 
        mock_market_status, 
        mock_timezone, 
        mock_tradier_client_class
    ):
        """Test end-to-end success scenario with minimal mocking."""
        # Setup mocks
        mock_client = Mock()
        mock_tradier_client_class.return_value = mock_client
        
        # Mock Tradier quote response
        from src.provider.tradier.client import TradierQuote
        mock_quote = TradierQuote(
            symbol="AAPL",
            last=150.25,
            change=2.15,
            change_percentage=1.45,
            high=152.00,
            low=149.50,
            open=150.00,
            prevclose=148.10,
            volume=75000000,
            description="Apple Inc"
        )
        
        mock_client.get_quotes.return_value = [mock_quote]
        mock_client.get_company_info.return_value = {}
        mock_client.get_ratios.return_value = {}
        
        # Mock time and market status
        mock_time = datetime(2023, 9, 25, 16, 0, 0)
        mock_timezone.return_value = mock_time
        mock_market_status.return_value = "closed"
        
        # Execute
        result = await get_stock_key_info("AAPL")
        
        # Verify success
        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        
        # Verify formatted info contains expected data
        formatted = result["formatted_info"]
        assert "AAPL (Apple Inc)" in formatted
        assert "$150.250" in formatted
        assert "+1.45%" in formatted
        
        # Verify raw data
        assert result["raw_data"]["price_data"]["close_price"] == 150.25
        assert result["raw_data"]["price_data"]["change_percentage"] == 1.45

    @pytest.mark.asyncio
    @patch('src.stock.info.TradierClient')
    async def test_end_to_end_tradier_api_error(self, mock_tradier_client_class):
        """Test end-to-end scenario with Tradier API error."""
        # Setup mock to fail
        mock_tradier_client_class.side_effect = ValueError("TRADIER_ACCESS_TOKEN environment variable is required")
        
        # Execute
        result = await get_stock_key_info("AAPL")
        
        # Verify error handling
        assert result["success"] is False
        assert "TRADIER_ACCESS_TOKEN" in result["error"]
        assert "❌ 无法获取 AAPL 的股票信息" in result["formatted_info"]