"""Tests for utils.time module."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from src.utils.time import get_timezone_time


class TestGetTimezoneTime:
    """Test the get_timezone_time function."""

    def test_utc_default(self):
        """Test that UTC is the default timezone."""
        result = get_timezone_time()
        assert result.tzinfo == ZoneInfo("UTC")

    def test_us_eastern(self):
        """Test US/Eastern timezone."""
        result = get_timezone_time("US/Eastern")
        assert result.tzinfo == ZoneInfo("US/Eastern")

    def test_asia_shanghai(self):
        """Test Asia/Shanghai timezone."""
        result = get_timezone_time("Asia/Shanghai")
        assert result.tzinfo == ZoneInfo("Asia/Shanghai")

    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises an error."""
        with pytest.raises(Exception):  # ZoneInfoNotFoundError
            get_timezone_time("Invalid/Timezone")

    def test_returns_datetime(self):
        """Test that function returns a datetime object."""
        result = get_timezone_time("UTC")
        assert isinstance(result, datetime)

    def test_time_is_recent(self):
        """Test that returned time is recent (within last minute)."""
        result = get_timezone_time("UTC")
        now = datetime.now(ZoneInfo("UTC"))
        time_diff = abs((now - result).total_seconds())
        assert time_diff < 60  # Within 1 minute