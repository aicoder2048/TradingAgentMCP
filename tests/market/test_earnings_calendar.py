"""Tests for earnings calendar functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.market.earnings_calendar import (
    get_earnings_calendar,
    is_earnings_related,
    is_recent_event,
    EarningsEvent,
    EarningsCalendarResponse,
    EARNINGS_KEYWORDS
)


class TestEarningsRelatedFiltering:
    """Test earnings event filtering functionality."""
    
    def test_is_earnings_related_with_earnings_keyword(self):
        """Test detection of earnings-related events."""
        assert is_earnings_related("Q1 2024 Earnings Call") is True
        assert is_earnings_related("Fourth Quarter Earnings Report") is True
        assert is_earnings_related("Annual Earnings Announcement") is True
        
    def test_is_earnings_related_with_quarter_keyword(self):
        """Test detection of quarterly reports."""
        assert is_earnings_related("Q3 Quarter Results") is True
        assert is_earnings_related("Quarterly Financial Results") is True
        
    def test_is_earnings_related_with_results_keyword(self):
        """Test detection of results announcements."""
        assert is_earnings_related("Financial Results Release") is True
        assert is_earnings_related("Annual Results Presentation") is True
        
    def test_is_earnings_related_case_insensitive(self):
        """Test case insensitive matching."""
        assert is_earnings_related("EARNINGS CALL") is True
        assert is_earnings_related("quarterly report") is True
        assert is_earnings_related("Fiscal YEAR results") is True
        
    def test_is_earnings_related_non_earnings_events(self):
        """Test rejection of non-earnings events."""
        assert is_earnings_related("Board Meeting") is False
        assert is_earnings_related("Stock Split") is False
        assert is_earnings_related("Dividend Payment") is False
        assert is_earnings_related("AGM Conference") is False
        
    def test_is_earnings_related_empty_or_none(self):
        """Test handling of empty or None descriptions."""
        assert is_earnings_related("") is False
        assert is_earnings_related(None) is False


class TestRecentEventFiltering:
    """Test recent event filtering functionality."""
    
    @patch('src.market.earnings_calendar.datetime')
    def test_is_recent_event_within_year(self, mock_datetime):
        """Test events within the past year are considered recent."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        # Test recent events (within 12 months)
        assert is_recent_event("2024-05-01") is True  # 1 month ago
        assert is_recent_event("2024-01-01") is True  # 5 months ago
        assert is_recent_event("2023-07-01") is True  # 11 months ago
    
    @patch('src.market.earnings_calendar.datetime')
    def test_is_recent_event_older_than_year(self, mock_datetime):
        """Test events older than a year are filtered out."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        # Test old events (older than 12 months)
        assert is_recent_event("2023-05-01") is False  # 13 months ago
        assert is_recent_event("2022-12-01") is False  # 18+ months ago
        assert is_recent_event("2021-01-01") is False  # Very old
    
    def test_is_recent_event_empty_or_invalid_date(self):
        """Test handling of empty or invalid dates."""
        assert is_recent_event("") is False
        assert is_recent_event(None) is False
        assert is_recent_event("invalid-date") is True  # Safe default
        assert is_recent_event("2024-13-45") is True  # Invalid but parsed safely
    
    @patch('src.market.earnings_calendar.datetime')
    def test_is_recent_event_future_dates(self, mock_datetime):
        """Test that future dates are considered recent."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        # Future dates should be considered recent
        assert is_recent_event("2024-07-01") is True  # Next month
        assert is_recent_event("2025-01-01") is True  # Next year


class TestEarningsCalendar:
    """Test earnings calendar data retrieval functionality."""

    def create_mock_corporate_calendar_response(self, events=None):
        """Helper to create mock corporate calendar response."""
        if events is None:
            events = []
            
        return {
            "type": "Symbol",
            "results": [
                {
                    "type": "Company",
                    "tables": {
                        "corporate_calendars": events
                    }
                }
            ]
        }

    def create_earnings_event(self, event_name, begin_date, **kwargs):
        """Helper to create earnings event data."""
        return {
            "event": event_name,
            "begin_date_time": begin_date,
            "end_date_time": kwargs.get("end_date", begin_date),
            "event_type": kwargs.get("event_type", 8),
            "event_fiscal_year": kwargs.get("fiscal_year", "2024"),
            "event_status": kwargs.get("status", "confirmed"),
            "estimated_date_for_next_event": kwargs.get("estimated_next_date")
        }

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.datetime')
    async def test_successful_earnings_calendar_retrieval(self, mock_datetime):
        """Test successful earnings calendar data retrieval."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        mock_client = Mock()
        mock_events = [
            self.create_earnings_event("Q1 2024 Earnings Call", "2024-04-25"),  # Recent earnings
            self.create_earnings_event("Q2 2024 Earnings Release", "2024-07-25"),  # Recent earnings
            self.create_earnings_event("Board Meeting", "2024-05-15")  # Not earnings, will be filtered out
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert result["total_events"] == 2  # Board meeting should be filtered out
        assert len(result["earnings_events"]) == 2
        
        # Check earnings events are properly filtered and sorted
        earnings_events = result["earnings_events"]
        assert "Earnings" in earnings_events[0]["event"]
        assert "Earnings" in earnings_events[1]["event"]
        
        # Verify chronological sorting (newest first)
        assert earnings_events[0]["begin_date"] >= earnings_events[1]["begin_date"]

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.datetime')
    async def test_next_earnings_date_calculation(self, mock_datetime):
        """Test calculation of next upcoming earnings date."""
        # Mock current date to be between the past and future dates
        mock_now = Mock()
        mock_now.strftime.return_value = "2024-06-01"
        mock_datetime.now.return_value = mock_now
        
        mock_client = Mock()
        future_date = "2025-01-25"  # Future date
        past_date = "2023-01-25"    # Past date
        
        mock_events = [
            self.create_earnings_event("Past Q1 Earnings", past_date),
            self.create_earnings_event("Future Q1 Earnings", future_date)
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        assert result["next_earnings_date"] == future_date

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.datetime')
    async def test_no_upcoming_earnings(self, mock_datetime):
        """Test when no upcoming earnings are available."""
        # Mock current date as 2024-06-01  
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        mock_client = Mock()
        # Use recent past dates that are within 12 months but still in the past
        past_date = "2024-01-25"  # Recent past (within 12 months)
        
        mock_events = [
            self.create_earnings_event("Past Q1 Earnings", past_date),
            self.create_earnings_event("Past Q2 Earnings", "2024-04-25")  # Recent past
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        assert result["next_earnings_date"] is None
        assert result["total_events"] == 2

    @pytest.mark.asyncio
    async def test_no_earnings_data_available(self):
        """Test handling when no earnings data is available."""
        mock_client = Mock()
        mock_client.get_corporate_calendar.return_value = None
        
        result = await get_earnings_calendar("INVALID", mock_client)
        
        assert result["symbol"] == "INVALID"
        assert result["provider"] == "TRADIER"
        assert result["earnings_events"] == []
        assert result["total_events"] == 0
        assert result["next_earnings_date"] is None
        assert "No calendar data available" in result["message"]

    @pytest.mark.asyncio
    async def test_empty_corporate_calendars(self):
        """Test handling when corporate calendars are empty."""
        mock_client = Mock()
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response([])
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        assert result["earnings_events"] == []
        assert result["total_events"] == 0
        assert "No earnings events found" in result["message"]

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test proper error handling for API failures."""
        mock_client = Mock()
        mock_client.get_corporate_calendar.side_effect = Exception("API Error")
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        assert "error" in result
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert result["earnings_events"] == []
        assert result["total_events"] == 0
        assert "Failed to fetch earnings calendar" in result["error"]
        assert "API Error" in result["details"]

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.TradierClient')
    async def test_client_initialization_failure(self, mock_tradier_client):
        """Test handling when TradierClient initialization fails."""
        # Make TradierClient initialization fail
        mock_tradier_client.side_effect = ValueError("TRADIER_ACCESS_TOKEN environment variable is required")
        
        # This should fail due to missing TRADIER_ACCESS_TOKEN
        result = await get_earnings_calendar("AAPL", None)
        
        # Should return error response rather than raise exception
        assert "error" in result
        assert "Failed to initialize Tradier client" in result["error"]
        assert result["symbol"] == "AAPL"
        assert result["provider"] == "TRADIER"
        assert result["earnings_events"] == []

    @pytest.mark.asyncio
    async def test_malformed_api_response(self):
        """Test handling of malformed API responses."""
        mock_client = Mock()
        # Malformed response missing expected structure
        mock_client.get_corporate_calendar.return_value = {"invalid": "structure"}
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        assert result["earnings_events"] == []
        assert result["total_events"] == 0

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.datetime')
    async def test_mixed_event_types_filtering(self, mock_datetime):
        """Test filtering of mixed event types."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        mock_client = Mock()
        mock_events = [
            self.create_earnings_event("Q1 2024 Earnings Call", "2024-04-25"),  # Recent earnings
            self.create_earnings_event("Dividend Declaration", "2024-05-01"),  # Not earnings (filtered out)
            self.create_earnings_event("Annual Earnings Results", "2024-03-15"),  # Recent earnings
            self.create_earnings_event("Board Meeting", "2024-06-01"),  # Not earnings (filtered out)
            self.create_earnings_event("Quarterly Report", "2024-07-15"),  # Recent earnings
            self.create_earnings_event("Old Earnings Call", "2022-01-01")  # Old earnings (filtered out by date)
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        # Should filter to only 3 earnings-related AND recent events
        assert result["total_events"] == 3
        assert len(result["earnings_events"]) == 3
        
        # Verify all events are earnings-related and recent
        for event in result["earnings_events"]:
            assert is_earnings_related(event["event"]) is True
            assert is_recent_event(event["begin_date"]) is True

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.datetime')
    async def test_old_earnings_events_filtered_out(self, mock_datetime):
        """Test that old earnings events (>1 year) are filtered out."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        mock_client = Mock()
        mock_events = [
            self.create_earnings_event("Q1 2024 Earnings Call", "2024-04-25"),  # Recent
            self.create_earnings_event("Q3 2023 Earnings Call", "2023-07-25"),  # Recent (within 11 months)  
            self.create_earnings_event("Q1 2022 Earnings Call", "2022-04-25"),  # Old (filtered out)
            self.create_earnings_event("Q1 2021 Earnings Call", "2021-04-25"),  # Very old (filtered out)
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        # Should only include recent earnings events (within 12 months)
        assert result["total_events"] == 2
        assert len(result["earnings_events"]) == 2
        
        # Verify all returned events are within the time range
        for event in result["earnings_events"]:
            event_date = event["begin_date"]
            assert event_date in ["2024-04-25", "2023-07-25"]

    @pytest.mark.asyncio
    @patch('src.market.earnings_calendar.datetime')
    async def test_event_sorting_chronological(self, mock_datetime):
        """Test events are sorted chronologically (newest first)."""
        # Mock current date as 2024-06-01
        mock_now = Mock()
        mock_now.strftime.return_value = "2024-06-01"
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime
        
        mock_client = Mock()
        mock_events = [
            self.create_earnings_event("Q2 2024 Earnings", "2024-07-25"),
            self.create_earnings_event("Q1 2024 Earnings", "2024-04-25"),
            self.create_earnings_event("Q3 2024 Earnings", "2024-10-25"),
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        events = result["earnings_events"]
        assert len(events) == 3
        
        # Should be sorted newest first
        assert events[0]["begin_date"] == "2024-10-25"  # Q3 (newest)
        assert events[1]["begin_date"] == "2024-07-25"  # Q2 
        assert events[2]["begin_date"] == "2024-04-25"  # Q1 (oldest)

    @pytest.mark.asyncio 
    @patch('src.market.earnings_calendar.datetime')
    async def test_comprehensive_event_data_mapping(self, mock_datetime):
        """Test comprehensive mapping of event data fields."""
        # Mock current date as 2024-06-01
        mock_now = datetime(2024, 6, 1)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        mock_client = Mock()
        mock_events = [
            {
                "event": "Q1 2024 Earnings Call",
                "begin_date_time": "2024-04-25",  # Recent date within 12 months
                "end_date_time": "2024-04-25",
                "event_type": 8,
                "event_fiscal_year": "2024",
                "event_status": "confirmed",
                "estimated_date_for_next_event": "2024-07-25"
            }
        ]
        mock_client.get_corporate_calendar.return_value = self.create_mock_corporate_calendar_response(mock_events)
        
        result = await get_earnings_calendar("AAPL", mock_client)
        
        event = result["earnings_events"][0]
        assert event["event"] == "Q1 2024 Earnings Call"
        assert event["begin_date"] == "2024-04-25"
        assert event["end_date"] == "2024-04-25"
        assert event["event_type"] == 8
        assert event["fiscal_year"] == "2024"
        assert event["status"] == "confirmed"
        assert event["estimated_next_date"] == "2024-07-25"


class TestDataStructures:
    """Test data structure definitions."""
    
    def test_earnings_event_creation(self):
        """Test EarningsEvent dataclass creation."""
        event = EarningsEvent(
            event="Q1 2024 Earnings Call",
            begin_date="2024-04-25",
            end_date="2024-04-25",
            event_type=8,
            fiscal_year="2024",
            status="confirmed",
            estimated_next_date="2024-07-25"
        )
        
        assert event.event == "Q1 2024 Earnings Call"
        assert event.begin_date == "2024-04-25"
        assert event.event_type == 8
        assert event.fiscal_year == "2024"

    def test_earnings_calendar_response_creation(self):
        """Test EarningsCalendarResponse dataclass creation."""
        response = EarningsCalendarResponse(
            symbol="AAPL",
            provider="TRADIER", 
            request_type="Symbol",
            earnings_events=[],
            total_events=0,
            next_earnings_date=None,
            message="No events found",
            error=None,
            details=None
        )
        
        assert response.symbol == "AAPL"
        assert response.provider == "TRADIER"
        assert response.total_events == 0
        assert response.message == "No events found"

    def test_earnings_keywords_defined(self):
        """Test earnings keywords are properly defined."""
        assert "earnings" in EARNINGS_KEYWORDS
        assert "quarter" in EARNINGS_KEYWORDS
        assert "results" in EARNINGS_KEYWORDS
        assert "quarterly" in EARNINGS_KEYWORDS
        assert len(EARNINGS_KEYWORDS) >= 4