"""Tests for market.hours module."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.market.hours import get_market_status, is_trading_day, get_next_trading_day


class TestGetMarketStatus:
    """Test the get_market_status function."""

    def test_premarket_hours(self):
        """Test pre-market detection (04:00-09:29 ET)."""
        # Monday 8:00 AM ET
        test_time = datetime(2025, 6, 16, 8, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(test_time) == "pre-market"

    def test_market_hours(self):
        """Test market hours detection (09:30-15:59 ET)."""
        # Monday 10:00 AM ET  
        test_time = datetime(2025, 6, 16, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(test_time) == "market"

    def test_after_hours(self):
        """Test after-hours detection (16:00-19:59 ET)."""
        # Monday 6:00 PM ET
        test_time = datetime(2025, 6, 16, 18, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(test_time) == "after-hours"

    def test_closed_hours_late_night(self):
        """Test closed detection during late night hours."""
        # Monday 11:00 PM ET
        test_time = datetime(2025, 6, 16, 23, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(test_time) == "closed"

    def test_weekend_closed(self):
        """Test that weekends are recognized as closed."""
        # Saturday 10:00 AM ET
        saturday = datetime(2025, 6, 21, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(saturday) == "closed"

        # Sunday 10:00 AM ET
        sunday = datetime(2025, 6, 22, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(sunday) == "closed"

    def test_holiday_closed(self):
        """Test that holidays are recognized as closed."""
        # New Year's Day 2025 (Wednesday) - should be closed even during market hours
        new_years = datetime(2025, 1, 1, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert get_market_status(new_years) == "closed"


class TestIsTradingDay:
    """Test the is_trading_day function."""

    def test_weekday_is_trading_day(self):
        """Test that weekdays are trading days."""
        # Monday
        monday = datetime(2025, 6, 16, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_trading_day(monday) is True

        # Friday
        friday = datetime(2025, 6, 20, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_trading_day(friday) is True

    def test_weekend_not_trading_day(self):
        """Test that weekends are not trading days."""
        # Saturday
        saturday = datetime(2025, 6, 21, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_trading_day(saturday) is False

        # Sunday
        sunday = datetime(2025, 6, 22, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_trading_day(sunday) is False

    def test_holiday_not_trading_day(self):
        """Test that holidays are not trading days."""
        # New Year's Day 2025
        new_years = datetime(2025, 1, 1, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_trading_day(new_years) is False

        # Christmas 2025
        christmas = datetime(2025, 12, 25, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_trading_day(christmas) is False


class TestGetNextTradingDay:
    """Test the get_next_trading_day function."""

    def test_next_trading_day_from_friday(self):
        """Test getting next trading day from Friday."""
        # Friday afternoon
        friday = datetime(2025, 6, 20, 16, 0, tzinfo=ZoneInfo("US/Eastern"))
        next_day = get_next_trading_day(friday)
        
        # Should be Monday at market open (9:30 AM)
        expected = datetime(2025, 6, 23, 9, 30, tzinfo=ZoneInfo("US/Eastern"))
        assert next_day == expected

    def test_next_trading_day_from_saturday(self):
        """Test getting next trading day from Saturday."""
        # Saturday
        saturday = datetime(2025, 6, 21, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        next_day = get_next_trading_day(saturday)
        
        # Should be Monday at market open
        expected = datetime(2025, 6, 23, 9, 30, tzinfo=ZoneInfo("US/Eastern"))
        assert next_day == expected

    def test_next_trading_day_from_holiday(self):
        """Test getting next trading day from a holiday."""
        # New Year's Day 2025 (Wednesday)
        new_years = datetime(2025, 1, 1, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        next_day = get_next_trading_day(new_years)
        
        # Should be Thursday at market open
        expected = datetime(2025, 1, 2, 9, 30, tzinfo=ZoneInfo("US/Eastern"))
        assert next_day == expected

    def test_next_trading_day_time_is_market_open(self):
        """Test that next trading day is always set to market open time."""
        # Any regular trading day
        tuesday = datetime(2025, 6, 17, 16, 0, tzinfo=ZoneInfo("US/Eastern"))
        next_day = get_next_trading_day(tuesday)
        
        # Time should be exactly 9:30 AM
        assert next_day.hour == 9
        assert next_day.minute == 30
        assert next_day.second == 0
        assert next_day.microsecond == 0