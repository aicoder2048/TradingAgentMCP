"""Tests for stock information processing."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.stock.info import StockInfo, StockInfoProcessor
from src.provider.tradier.client import TradierQuote


class TestStockInfo:
    """Test suite for StockInfo dataclass."""
    
    def test_stock_info_creation_minimal(self):
        """Test creating StockInfo with minimal required fields."""
        stock_info = StockInfo(
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
            volume=93133600
        )
        
        assert stock_info.symbol == "TSLA"
        assert stock_info.company_name == "Tesla Inc"
        assert stock_info.close_price == 442.79
        assert stock_info.change_percentage == 3.98
        assert stock_info.volume == 93133600
        assert stock_info.lot_size == 1  # Default value
    
    def test_stock_info_creation_full(self):
        """Test creating StockInfo with all fields."""
        stock_info = StockInfo(
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
            turnover_amount=4.08e10,
            turnover_rate=3.35,
            pe_ratio_ttm=263.57,
            pb_ratio=19.04,
            market_cap=1.47e12,
            week_52_high=488.54,
            week_52_low=212.11,
            beta=2.334,
            amplitude=3.57,
            premarket_price=440.68,
            premarket_change=-2.11,
            premarket_change_percentage=-0.48,
            market_status="closed"
        )
        
        assert stock_info.pe_ratio_ttm == 263.57
        assert stock_info.market_cap == 1.47e12
        assert stock_info.beta == 2.334
        assert stock_info.premarket_price == 440.68
        assert stock_info.market_status == "closed"


class TestStockInfoProcessor:
    """Test suite for StockInfoProcessor."""
    
    @pytest.fixture
    def mock_tradier_client(self):
        """Mock Tradier client."""
        return Mock()
    
    @pytest.fixture
    def processor(self, mock_tradier_client):
        """Create processor with mock client."""
        with patch('src.stock.info.TradierClient', return_value=mock_tradier_client):
            return StockInfoProcessor()
    
    @pytest.fixture
    def mock_quote(self):
        """Create mock TradierQuote."""
        return TradierQuote(
            symbol="TSLA",
            last=442.79,
            change=16.94,
            change_percentage=3.98,
            high=444.21,
            low=429.03,
            open=429.83,
            prevclose=425.85,
            volume=93133600,
            description="Tesla Inc",
            bid=442.50,
            ask=442.80
        )
    
    @pytest.fixture
    def mock_eastern_time(self):
        """Mock Eastern time."""
        return datetime(2023, 9, 25, 16, 0, 0)
    
    @patch('src.stock.info.get_timezone_time')
    @patch('src.stock.info.get_market_status')
    async def test_get_stock_info_success(
        self, 
        mock_market_status, 
        mock_timezone, 
        processor, 
        mock_quote,
        mock_eastern_time
    ):
        """Test successful stock info retrieval."""
        # Setup mocks
        mock_timezone.return_value = mock_eastern_time
        mock_market_status.return_value = "closed"
        
        processor.tradier_client.get_quotes.return_value = [mock_quote]
        processor.tradier_client.get_company_info.return_value = {}
        processor.tradier_client.get_ratios.return_value = {}
        
        # Execute
        stock_info = await processor.get_stock_info("TSLA")
        
        # Verify
        assert stock_info.symbol == "TSLA"
        assert stock_info.company_name == "Tesla Inc"
        assert stock_info.close_price == 442.79
        assert stock_info.change_amount == 16.94
        assert stock_info.change_percentage == 3.98
        assert stock_info.volume == 93133600
        assert stock_info.market_status == "closed"
        
        # Verify API calls
        processor.tradier_client.get_quotes.assert_called_once_with(["TSLA"])
        processor.tradier_client.get_company_info.assert_called_once_with("TSLA")
        processor.tradier_client.get_ratios.assert_called_once_with("TSLA")
    
    @patch('src.stock.info.get_timezone_time')
    @patch('src.stock.info.get_market_status')
    async def test_get_stock_info_no_data(
        self, 
        mock_market_status, 
        mock_timezone, 
        processor,
        mock_eastern_time
    ):
        """Test handling when no quote data is returned."""
        # Setup mocks
        mock_timezone.return_value = mock_eastern_time
        mock_market_status.return_value = "closed"
        processor.tradier_client.get_quotes.return_value = []
        
        # Execute and verify exception
        with pytest.raises(Exception, match="Failed to fetch stock info for INVALID: No data found for symbol: INVALID"):
            await processor.get_stock_info("INVALID")
    
    @patch('src.stock.info.get_timezone_time')
    @patch('src.stock.info.get_market_status')
    async def test_get_stock_info_with_ratios(
        self, 
        mock_market_status, 
        mock_timezone, 
        processor, 
        mock_quote,
        mock_eastern_time
    ):
        """Test stock info retrieval with financial ratios."""
        # Setup mocks
        mock_timezone.return_value = mock_eastern_time
        mock_market_status.return_value = "market"
        
        mock_ratios = {
            "results": [
                {
                    "tables": {
                        "operation_ratios_restate": [
                            {
                                "period_3m": {
                                    "as_of_date": "2025-06-30",
                                    "r_o_e": 0.25,
                                    "r_o_a": 0.15
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        processor.tradier_client.get_quotes.return_value = [mock_quote]
        processor.tradier_client.get_company_info.return_value = {}
        processor.tradier_client.get_ratios.return_value = mock_ratios
        
        # Execute
        stock_info = await processor.get_stock_info("TSLA")
        
        # Verify stock info structure - Note: PE ratios not available in current API
        assert stock_info.pe_ratio_ttm is None  # Not available in operation_ratios_restate
        assert stock_info.pb_ratio is None      # Not available in operation_ratios_restate
        assert stock_info.market_cap is None    # Not available in operation_ratios_restate
        assert stock_info.beta is None          # Not available in operation_ratios_restate
        assert stock_info.market_status == "market"
    
    @patch('src.stock.info.get_timezone_time')
    @patch('src.stock.info.get_market_status')
    async def test_get_stock_info_api_error(
        self, 
        mock_market_status, 
        mock_timezone, 
        processor,
        mock_eastern_time
    ):
        """Test handling API errors gracefully."""
        # Setup mocks
        mock_timezone.return_value = mock_eastern_time
        mock_market_status.return_value = "closed"
        processor.tradier_client.get_quotes.side_effect = Exception("API Error")
        
        # Execute and verify exception propagation
        with pytest.raises(Exception, match="Failed to fetch stock info for TSLA: API Error"):
            await processor.get_stock_info("TSLA")
    
    def test_build_stock_info_amplitude_calculation(self, processor):
        """Test amplitude calculation in _build_stock_info."""
        quote = TradierQuote(
            symbol="TSLA",
            last=442.79,
            high=444.21,
            low=429.03,
            prevclose=425.85,
            change=16.94,
            change_percentage=3.98,
            volume=93133600
        )
        
        eastern_time = datetime(2023, 9, 25, 16, 0, 0)
        
        stock_info = processor._build_stock_info(
            quote=quote,
            company_info={},
            ratios={},
            market_status="closed",
            eastern_time=eastern_time
        )
        
        # Verify amplitude calculation: ((444.21 - 429.03) / 425.85) * 100 ≈ 3.57%
        expected_amplitude = ((444.21 - 429.03) / 425.85) * 100
        assert abs(stock_info.amplitude - expected_amplitude) < 0.01
    
    def test_build_stock_info_average_price_calculation(self, processor):
        """Test average price calculation."""
        quote = TradierQuote(
            symbol="TSLA",
            last=442.79,
            high=444.21,
            low=429.03,
            prevclose=425.85
        )
        
        eastern_time = datetime(2023, 9, 25, 16, 0, 0)
        
        stock_info = processor._build_stock_info(
            quote=quote,
            company_info={},
            ratios={},
            market_status="closed",
            eastern_time=eastern_time
        )
        
        # Verify average price: (444.21 + 429.03) / 2 = 436.62
        expected_avg = (444.21 + 429.03) / 2
        assert stock_info.average_price == expected_avg
    
    def test_get_price_time_label(self, processor):
        """Test price time label generation."""
        eastern_time = datetime(2023, 9, 25, 16, 0, 0)
        
        # Test different market statuses
        assert "实时" in processor._get_price_time_label("market", eastern_time)
        assert "盘前" in processor._get_price_time_label("pre-market", eastern_time)
        assert "盘后" in processor._get_price_time_label("after-hours", eastern_time)
        assert "收盘" in processor._get_price_time_label("closed", eastern_time)
    
    def test_format_stock_info_basic(self, processor):
        """Test basic stock info formatting."""
        stock_info = StockInfo(
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
            amplitude=3.57,
            lot_size=1
        )
        
        formatted = processor.format_stock_info(stock_info)
        
        # Verify key elements are present
        assert "TSLA (Tesla Inc)" in formatted
        assert "$442.790" in formatted
        assert "+3.98%" in formatted
        assert "9313.36万股" in formatted  # Volume formatting
        assert "振幅: 3.57%" in formatted
        assert "每手: 1股" in formatted
    
    def test_format_stock_info_with_valuation(self, processor):
        """Test stock info formatting with valuation metrics."""
        stock_info = StockInfo(
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
            pe_ratio_ttm=263.57,
            pb_ratio=19.04,
            market_cap=1.47e12,
            beta=2.334
        )
        
        formatted = processor.format_stock_info(stock_info)
        
        # Verify valuation section is present
        assert "估值指标" in formatted
        assert "市盈率TTM: 263.57" in formatted
        assert "市净率: 19.04" in formatted
        assert "1.47万亿" in formatted  # Market cap formatting
        assert "Beta系数: 2.334" in formatted
    
    def test_format_stock_info_with_premarket(self, processor):
        """Test stock info formatting with pre-market data."""
        stock_info = StockInfo(
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
            premarket_price=440.68,
            premarket_change=-2.11,
            premarket_change_percentage=-0.48,
            premarket_time="06:36 (美东)"
        )
        
        formatted = processor.format_stock_info(stock_info)
        
        # Verify pre-market section is present
        assert "盘前交易" in formatted
        assert "盘前价格: $440.680" in formatted
        assert "盘前变动: $-2.110 (-0.48%)" in formatted
        assert "盘前时间: 06:36 (美东)" in formatted
    
    def test_get_raw_data_dict(self, processor):
        """Test conversion to raw data dictionary."""
        stock_info = StockInfo(
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
            market_status="closed",
            data_timestamp="2023-09-25T20:00:00"
        )
        
        raw_data = processor.get_raw_data_dict(stock_info)
        
        # Verify structure
        assert "symbol" in raw_data
        assert "price_data" in raw_data
        assert "trading_data" in raw_data
        assert "valuation_metrics" in raw_data
        assert "technical_indicators" in raw_data
        assert "premarket_data" in raw_data
        assert "context" in raw_data
        
        # Verify data
        assert raw_data["symbol"] == "TSLA"
        assert raw_data["price_data"]["close_price"] == 442.79
        assert raw_data["trading_data"]["volume"] == 93133600
        assert raw_data["context"]["market_status"] == "closed"


class TestStockInfoFormattingHelpers:
    """Test formatting helper functions indirectly."""
    
    @patch('src.stock.info.TradierClient')
    def test_large_number_formatting_via_format_stock_info(self, mock_client):
        """Test large number formatting through format_stock_info."""
        processor = StockInfoProcessor()
        
        # Test various volume sizes
        test_cases = [
            (1234, "1,234股"),  # Small numbers use comma formatting
            (12345, "1.23万股"),
            (123456789, "1.23亿股"),
            (1234567890123, "1.23万亿股")
        ]
        
        for volume, expected in test_cases:
            stock_info = StockInfo(
                symbol="TEST",
                company_name="Test Inc",
                close_price=100.0,
                close_time="test",
                change_amount=0.0,
                change_percentage=0.0,
                high_price=100.0,
                low_price=100.0,
                open_price=100.0,
                prev_close=100.0,
                volume=volume
            )
            
            formatted = processor.format_stock_info(stock_info)
            assert expected in formatted
    
    @patch('src.stock.info.TradierClient')
    def test_percentage_formatting_via_format_stock_info(self, mock_client):
        """Test percentage formatting through format_stock_info."""
        processor = StockInfoProcessor()
        
        test_cases = [
            (3.98, "+3.98%"),
            (-2.15, "-2.15%"),
            (0.0, "+0.00%")
        ]
        
        for change_pct, expected in test_cases:
            stock_info = StockInfo(
                symbol="TEST",
                company_name="Test Inc", 
                close_price=100.0,
                close_time="test",
                change_amount=0.0,
                change_percentage=change_pct,
                high_price=100.0,
                low_price=100.0,
                open_price=100.0,
                prev_close=100.0,
                volume=1000
            )
            
            formatted = processor.format_stock_info(stock_info)
            assert expected in formatted