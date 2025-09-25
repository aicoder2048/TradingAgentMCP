"""Tests for market.holidays module."""

import pytest
from datetime import datetime, date
from zoneinfo import ZoneInfo
from src.market.holidays import load_holidays, is_market_holiday


class TestLoadHolidays:
    """Test the load_holidays function."""

    def test_load_2025_2026_holidays(self):
        """Test loading holidays for 2025-2026 range."""
        holidays = load_holidays("2025_2026")
        
        # Should be a set of date objects
        assert isinstance(holidays, set)
        assert all(isinstance(h, date) for h in holidays)
        
        # Check for some known holidays
        assert date(2025, 1, 1) in holidays  # New Year's Day 2025
        assert date(2025, 12, 25) in holidays  # Christmas 2025
        assert date(2026, 1, 1) in holidays  # New Year's Day 2026

    def test_caching_works(self):
        """Test that holiday data is cached properly."""
        # First call
        holidays1 = load_holidays("2025_2026")
        
        # Second call should return cached data (same object)
        holidays2 = load_holidays("2025_2026")
        
        assert holidays1 is holidays2  # Same object reference

    def test_invalid_year_range_raises_error(self):
        """Test that invalid year range raises an error."""
        with pytest.raises(FileNotFoundError):
            load_holidays("invalid_range")


class TestIsMarketHoliday:
    """Test the is_market_holiday function."""

    def test_new_years_day_2025(self):
        """Test that New Year's Day 2025 is recognized as holiday."""
        new_years = datetime(2025, 1, 1, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(new_years) is True

    def test_martin_luther_king_day_2025(self):
        """Test that MLK Day 2025 is recognized as holiday."""
        mlk_day = datetime(2025, 1, 20, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(mlk_day) is True

    def test_christmas_2025(self):
        """Test that Christmas 2025 is recognized as holiday."""
        christmas = datetime(2025, 12, 25, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(christmas) is True

    def test_regular_weekday_not_holiday(self):
        """Test that regular weekdays are not holidays."""
        # Random Tuesday in June
        regular_day = datetime(2025, 6, 17, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(regular_day) is False

    def test_weekend_not_holiday_by_definition(self):
        """Test that weekends are not considered holidays in this function."""
        # Saturday (even though market is closed)
        saturday = datetime(2025, 6, 21, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(saturday) is False

    def test_year_outside_data_range_returns_false(self):
        """Test that years outside our data range return False."""
        # Year 2024 - should return False as we only have 2025-2026 data
        old_date = datetime(2024, 1, 1, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(old_date) is False
        
        # Year 2027 - should return False as we only have 2025-2026 data
        future_date = datetime(2027, 1, 1, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(future_date) is False

    def test_independence_day_observed(self):
        """Test that Independence Day observed 2026 is recognized."""
        # July 3, 2026 (Independence Day observed)
        july_4_observed = datetime(2026, 7, 3, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(july_4_observed) is True

    def test_thanksgiving_2025(self):
        """Test that Thanksgiving 2025 is recognized."""
        thanksgiving = datetime(2025, 11, 27, 10, 0, tzinfo=ZoneInfo("US/Eastern"))
        assert is_market_holiday(thanksgiving) is True