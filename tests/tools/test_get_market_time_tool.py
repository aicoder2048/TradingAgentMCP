"""Tests for get_market_time_tool."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from src.mcp_server.tools.get_market_time_tool import get_market_time_status


class TestGetMarketTimeStatus:
    """Test the get_market_time_status MCP tool."""

    @pytest.mark.asyncio
    async def test_successful_response_structure(self):
        """Test that the tool returns the expected response structure."""
        result = await get_market_time_status()
        
        # Should be a dictionary
        assert isinstance(result, dict)
        
        # Should not have error field if successful
        assert "error" not in result
        
        # Should have required fields
        required_fields = ["eastern_time", "market_status", "is_trading_day", "timestamp"]
        for field in required_fields:
            assert field in result

    @pytest.mark.asyncio
    async def test_eastern_time_format(self):
        """Test that eastern_time is in proper ISO format."""
        result = await get_market_time_status()
        
        # Should be able to parse as ISO datetime
        eastern_time_str = result["eastern_time"]
        parsed_time = datetime.fromisoformat(eastern_time_str)
        
        # Should be timezone-aware
        assert parsed_time.tzinfo is not None

    @pytest.mark.asyncio
    async def test_market_status_values(self):
        """Test that market_status returns valid values."""
        result = await get_market_time_status()
        
        valid_statuses = ["pre-market", "market", "after-hours", "closed"]
        assert result["market_status"] in valid_statuses

    @pytest.mark.asyncio
    async def test_is_trading_day_is_boolean(self):
        """Test that is_trading_day is a boolean."""
        result = await get_market_time_status()
        
        assert isinstance(result["is_trading_day"], bool)

    @pytest.mark.asyncio
    async def test_timestamp_format(self):
        """Test that timestamp is in proper UTC format."""
        result = await get_market_time_status()
        
        # Should end with '+00:00' indicating UTC
        assert result["timestamp"].endswith("+00:00")
        
        # Should be parseable as ISO datetime
        parsed_time = datetime.fromisoformat(result["timestamp"])
        assert parsed_time.tzinfo is not None

    @pytest.mark.asyncio
    async def test_next_trading_day_when_not_trading(self):
        """Test that next_trading_day is included when not a trading day."""
        # Mock a weekend day (Saturday)
        mock_saturday = datetime(2025, 6, 21, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        
        with patch('src.mcp_server.tools.get_market_time_tool.get_timezone_time', return_value=mock_saturday):
            result = await get_market_time_status()
            
            # Should include next_trading_day since it's weekend
            assert "next_trading_day" in result
            assert result["is_trading_day"] is False

    @pytest.mark.asyncio
    async def test_no_next_trading_day_when_trading(self):
        """Test that next_trading_day is not included when it's a trading day."""
        # Mock a weekday (Monday)
        mock_monday = datetime(2025, 6, 16, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        
        with patch('src.mcp_server.tools.get_market_time_tool.get_timezone_time', return_value=mock_monday):
            result = await get_market_time_status()
            
            # Should not include next_trading_day since it's a trading day
            assert result["is_trading_day"] is True
            # next_trading_day should not be present or be None
            assert "next_trading_day" not in result

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that errors are properly handled and returned."""
        # Mock an exception in get_timezone_time
        with patch('src.mcp_server.tools.get_market_time_tool.get_timezone_time', side_effect=Exception("Test error")):
            result = await get_market_time_status()
            
            # Should have error field
            assert "error" in result
            assert result["error"] == "Test error"
            
            # Should still have timestamp
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_market_hours_scenarios(self):
        """Test different market hours scenarios."""
        test_cases = [
            # Pre-market: Monday 8:00 AM ET
            (datetime(2025, 6, 16, 8, 0, tzinfo=ZoneInfo("US/Eastern")), "pre-market", True),
            # Market: Monday 10:00 AM ET
            (datetime(2025, 6, 16, 10, 0, tzinfo=ZoneInfo("US/Eastern")), "market", True),
            # After-hours: Monday 6:00 PM ET
            (datetime(2025, 6, 16, 18, 0, tzinfo=ZoneInfo("US/Eastern")), "after-hours", True),
            # Closed: Monday 11:00 PM ET
            (datetime(2025, 6, 16, 23, 0, tzinfo=ZoneInfo("US/Eastern")), "closed", True),
            # Weekend: Saturday 10:00 AM ET
            (datetime(2025, 6, 21, 10, 0, tzinfo=ZoneInfo("US/Eastern")), "closed", False),
        ]
        
        for test_time, expected_status, expected_trading_day in test_cases:
            with patch('src.mcp_server.tools.get_market_time_tool.get_timezone_time', return_value=test_time):
                result = await get_market_time_status()
                
                assert result["market_status"] == expected_status
                assert result["is_trading_day"] == expected_trading_day

    @pytest.mark.asyncio
    async def test_response_consistency(self):
        """Test that multiple calls return consistent structure."""
        result1 = await get_market_time_status()
        result2 = await get_market_time_status()
        
        # Both should have same keys (except timestamps will differ)
        keys1 = set(result1.keys())
        keys2 = set(result2.keys())
        
        # Remove timestamp for comparison as it will be different
        keys1.discard("timestamp")
        keys2.discard("timestamp")
        
        assert keys1 == keys2