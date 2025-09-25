"""Tests for earnings calendar MCP tool."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timezone
from src.mcp_server.tools.get_earnings_calendar_tool import get_earnings_calendar_tool


class TestEarningsCalendarTool:
    """Test suite for get_earnings_calendar_tool MCP tool."""

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_get_earnings_calendar_tool_success(self, mock_get_calendar, mock_tradier_class):
        """Test successful earnings calendar retrieval."""
        # Setup mock calendar response
        mock_calendar_data = {
            "symbol": "AAPL",
            "provider": "TRADIER",
            "request_type": "Symbol",
            "earnings_events": [
                {
                    "event": "Q1 2024 Earnings Call",
                    "begin_date": "2024-04-25",
                    "end_date": "2024-04-25",
                    "event_type": 8,
                    "fiscal_year": "2024",
                    "status": "confirmed",
                    "estimated_next_date": "2024-07-25"
                },
                {
                    "event": "Q4 2023 Results",
                    "begin_date": "2024-01-25",
                    "end_date": "2024-01-25",
                    "event_type": 8,
                    "fiscal_year": "2023",
                    "status": "confirmed",
                    "estimated_next_date": "2024-04-25"
                }
            ],
            "total_events": 2,
            "next_earnings_date": "2024-04-25"
        }
        
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = mock_calendar_data
        
        # Execute
        result = await get_earnings_calendar_tool("aapl")  # Test case conversion
        
        # Verify response structure
        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert result["request_type"] == "Symbol"
        assert "timestamp" in result
        assert "error" not in result
        
        # Verify earnings events
        assert len(result["earnings_events"]) == 2
        assert result["total_events"] == 2
        assert result["next_earnings_date"] == "2024-04-25"
        
        # Verify earnings event details
        first_event = result["earnings_events"][0]
        assert first_event["event"] == "Q1 2024 Earnings Call"
        assert first_event["begin_date"] == "2024-04-25"
        assert first_event["fiscal_year"] == "2024"
        assert first_event["status"] == "confirmed"
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        assert timestamp.tzinfo is not None
        
        # Verify function calls
        mock_get_calendar.assert_called_once_with("AAPL", mock_client)

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_get_earnings_calendar_tool_no_events(self, mock_get_calendar, mock_tradier_class):
        """Test handling when no earnings events are found."""
        # Setup mock response with no events
        mock_calendar_data = {
            "symbol": "UNKNOWN",
            "provider": "TRADIER",
            "request_type": "Symbol",
            "earnings_events": [],
            "total_events": 0,
            "next_earnings_date": None,
            "message": "No earnings events found for UNKNOWN. This could mean the company doesn't report earnings regularly or the data is not available in Tradier's corporate calendar."
        }
        
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = mock_calendar_data
        
        # Execute
        result = await get_earnings_calendar_tool("UNKNOWN")
        
        # Verify response
        assert result["success"] is True
        assert result["symbol"] == "UNKNOWN"
        assert result["earnings_events"] == []
        assert result["total_events"] == 0
        assert result["next_earnings_date"] is None
        assert "No earnings events found" in result["message"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_get_earnings_calendar_tool_api_error(self, mock_get_calendar, mock_tradier_class):
        """Test handling of API errors from underlying calendar function."""
        # Setup mock to return error response
        mock_calendar_data = {
            "error": "Failed to fetch earnings calendar for INVALID",
            "details": "Symbol not found in Tradier API",
            "symbol": "INVALID",
            "provider": "TRADIER"
        }
        
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = mock_calendar_data
        
        # Execute
        result = await get_earnings_calendar_tool("INVALID")
        
        # Verify error response
        assert result["success"] is False
        assert result["symbol"] == "INVALID"
        assert result["provider"] == "TRADIER"
        assert result["error"] == "Failed to fetch earnings calendar for INVALID"
        assert result["details"] == "Symbol not found in Tradier API"
        assert result["earnings_events"] == []
        assert result["total_events"] == 0
        assert result["next_earnings_date"] is None
        assert "timestamp" in result

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    async def test_get_earnings_calendar_tool_client_initialization_error(self, mock_tradier_class):
        """Test handling of Tradier client initialization errors."""
        # Make TradierClient initialization fail
        mock_tradier_class.side_effect = ValueError("TRADIER_ACCESS_TOKEN environment variable is required")
        
        # Execute
        result = await get_earnings_calendar_tool("AAPL")
        
        # Verify error handling
        assert result["success"] is False
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert "TRADIER_ACCESS_TOKEN" in result["details"]
        assert "Failed to fetch earnings calendar for AAPL" in result["error"]
        assert result["earnings_events"] == []

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_get_earnings_calendar_tool_calendar_function_error(self, mock_get_calendar, mock_tradier_class):
        """Test handling of errors from get_earnings_calendar function."""
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.side_effect = Exception("Network timeout error")
        
        # Execute
        result = await get_earnings_calendar_tool("AAPL")
        
        # Verify error handling
        assert result["success"] is False
        assert result["symbol"] == "AAPL"
        assert "Failed to fetch earnings calendar for AAPL" in result["error"]
        assert "Network timeout error" in result["details"]
        assert result["earnings_events"] == []

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_symbol_normalization(self, mock_get_calendar, mock_tradier_class):
        """Test that symbols are properly normalized to uppercase."""
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = {
            "symbol": "TSLA",
            "provider": "TRADIER",
            "earnings_events": [],
            "total_events": 0
        }
        
        # Test various case inputs
        test_cases = ["tsla", "Tsla", "TSLA", "tSlA", "  TSLA  "]
        
        for input_symbol in test_cases:
            # Execute
            result = await get_earnings_calendar_tool(input_symbol)
            
            # Verify symbol normalization
            assert result["symbol"] == "TSLA"
            mock_get_calendar.assert_called_with("TSLA", mock_client)

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_comprehensive_earnings_data(self, mock_get_calendar, mock_tradier_class):
        """Test handling of comprehensive earnings data."""
        # Setup comprehensive mock response
        mock_calendar_data = {
            "symbol": "NVDA",
            "provider": "TRADIER",
            "request_type": "Symbol",
            "earnings_events": [
                {
                    "event": "Q3 2024 Earnings Call",
                    "begin_date": "2024-11-20",
                    "end_date": "2024-11-20",
                    "event_type": 8,
                    "fiscal_year": "2024",
                    "status": "confirmed",
                    "estimated_next_date": "2025-02-20"
                },
                {
                    "event": "Q2 2024 Results Announcement",
                    "begin_date": "2024-08-28",
                    "end_date": "2024-08-28",
                    "event_type": 8,
                    "fiscal_year": "2024",
                    "status": "completed",
                    "estimated_next_date": "2024-11-20"
                },
                {
                    "event": "Q1 2024 Quarterly Report", 
                    "begin_date": "2024-05-22",
                    "end_date": "2024-05-22",
                    "event_type": 8,
                    "fiscal_year": "2024",
                    "status": "completed",
                    "estimated_next_date": "2024-08-28"
                }
            ],
            "total_events": 3,
            "next_earnings_date": "2024-11-20"
        }
        
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = mock_calendar_data
        
        # Execute
        result = await get_earnings_calendar_tool("NVDA")
        
        # Verify comprehensive data handling
        assert result["success"] is True
        assert result["symbol"] == "NVDA"
        assert len(result["earnings_events"]) == 3
        assert result["total_events"] == 3
        assert result["next_earnings_date"] == "2024-11-20"
        
        # Verify individual event details
        events = result["earnings_events"]
        assert events[0]["event"] == "Q3 2024 Earnings Call"
        assert events[1]["event"] == "Q2 2024 Results Announcement"
        assert events[2]["event"] == "Q1 2024 Quarterly Report"
        
        # Verify all events have required fields
        for event in events:
            assert "event" in event
            assert "begin_date" in event
            assert "fiscal_year" in event
            assert "status" in event

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_upcoming_vs_historical_earnings(self, mock_get_calendar, mock_tradier_class):
        """Test handling of mixed upcoming and historical earnings."""
        # Setup mock with mixed dates
        mock_calendar_data = {
            "symbol": "META",
            "provider": "TRADIER",
            "request_type": "Symbol",
            "earnings_events": [
                {
                    "event": "Q4 2024 Earnings (Future)",
                    "begin_date": "2025-01-30",  # Future
                    "end_date": "2025-01-30",
                    "event_type": 8,
                    "fiscal_year": "2024",
                    "status": "scheduled",
                    "estimated_next_date": None
                },
                {
                    "event": "Q3 2024 Earnings (Past)",
                    "begin_date": "2023-10-25",  # Past
                    "end_date": "2023-10-25",
                    "event_type": 8,
                    "fiscal_year": "2024", 
                    "status": "completed",
                    "estimated_next_date": "2025-01-30"
                }
            ],
            "total_events": 2,
            "next_earnings_date": "2025-01-30"
        }
        
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = mock_calendar_data
        
        # Execute
        result = await get_earnings_calendar_tool("META")
        
        # Verify mixed date handling
        assert result["success"] is True
        assert result["next_earnings_date"] == "2025-01-30"
        assert result["total_events"] == 2
        
        # Verify events are present
        events = result["earnings_events"]
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_timestamp_format(self):
        """Test that timestamps are in correct ISO format with timezone."""
        with patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient') as mock_tradier_class:
            # Setup mock to trigger error path (which also generates timestamp)
            mock_tradier_class.side_effect = Exception("Test error")
            
            # Execute
            result = await get_earnings_calendar_tool("TEST")
            
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
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.TradierClient')
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_empty_symbol_handling(self, mock_get_calendar, mock_tradier_class):
        """Test handling of empty or whitespace symbols."""
        # Setup mocks
        mock_client = Mock()
        mock_tradier_class.return_value = mock_client
        mock_get_calendar.return_value = {
            "error": "Invalid symbol",
            "symbol": "",
            "provider": "TRADIER"
        }
        
        # Test empty and whitespace symbols
        test_cases = ["", "   ", "\t", "\n"]
        
        for empty_symbol in test_cases:
            result = await get_earnings_calendar_tool(empty_symbol)
            
            # Should handle gracefully
            assert result["success"] is False
            assert "error" in result


class TestEarningsCalendarToolIntegration:
    """Integration tests for earnings calendar tool."""

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_end_to_end_success_scenario(self, mock_get_calendar):
        """Test end-to-end success scenario with minimal mocking."""
        # Setup mock calendar response
        mock_calendar_data = {
            "symbol": "AAPL",
            "provider": "TRADIER",
            "request_type": "Symbol",
            "earnings_events": [
                {
                    "event": "Q1 2024 Earnings Call",
                    "begin_date": "2024-04-25",
                    "end_date": "2024-04-25",
                    "event_type": 8,
                    "fiscal_year": "2024",
                    "status": "confirmed",
                    "estimated_next_date": "2024-07-25"
                }
            ],
            "total_events": 1,
            "next_earnings_date": "2024-04-25"
        }
        
        mock_get_calendar.return_value = mock_calendar_data
        
        # Execute
        result = await get_earnings_calendar_tool("AAPL")
        
        # Verify end-to-end success
        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        
        # Verify filtering worked (should have 1 event)
        assert result["total_events"] == 1
        assert len(result["earnings_events"]) == 1
        assert result["earnings_events"][0]["event"] == "Q1 2024 Earnings Call"

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_end_to_end_api_error(self, mock_get_calendar):
        """Test end-to-end scenario with API error."""
        # Setup mock to return error response
        mock_get_calendar.return_value = {
            "error": "Failed to fetch earnings calendar for AAPL",
            "details": "TRADIER_ACCESS_TOKEN environment variable is required",
            "symbol": "AAPL",
            "provider": "TRADIER"
        }
        
        # Execute
        result = await get_earnings_calendar_tool("AAPL")
        
        # Verify error handling
        assert result["success"] is False
        assert "TRADIER_ACCESS_TOKEN" in result["details"]
        assert "Failed to fetch earnings calendar" in result["error"]

    @pytest.mark.asyncio
    @patch('src.mcp_server.tools.get_earnings_calendar_tool.get_earnings_calendar')
    async def test_end_to_end_no_data_scenario(self, mock_get_calendar):
        """Test end-to-end scenario when no calendar data is available."""
        # Setup mock to return no data response
        mock_get_calendar.return_value = {
            "symbol": "UNKNOWN",
            "provider": "TRADIER",
            "request_type": "Symbol",
            "earnings_events": [],
            "total_events": 0,
            "next_earnings_date": None,
            "message": "No calendar data available for UNKNOWN. This could mean the company doesn't report earnings regularly or the data is not available in Tradier's corporate calendar."
        }
        
        # Execute
        result = await get_earnings_calendar_tool("UNKNOWN")
        
        # Verify no data handling
        assert result["success"] is True
        assert result["earnings_events"] == []
        assert result["total_events"] == 0
        assert result["next_earnings_date"] is None
        assert "No calendar data available" in result["message"]