"""Holiday management for US stock market."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Set

_HOLIDAYS_CACHE: dict[str, Set[date]] = {}


def load_holidays(year_range: str) -> Set[date]:
    """
    Load holidays for a specific year range.

    Args:
        year_range: Year range string (e.g., "2025_2026")

    Returns:
        Set of holiday dates
    """
    if year_range in _HOLIDAYS_CACHE:
        return _HOLIDAYS_CACHE[year_range]

    data_dir = Path(__file__).parent / "data"
    file_path = data_dir / f"mkt_holidays_{year_range}.json"

    with open(file_path, 'r') as f:
        data = json.load(f)
        holidays = {
            datetime.strptime(h["date"], "%Y-%m-%d").date()
            for h in data["holidays"]
        }

    _HOLIDAYS_CACHE[year_range] = holidays
    return holidays


def is_market_holiday(check_date: datetime) -> bool:
    """
    Check if a given date is a US market holiday.

    Args:
        check_date: Date to check

    Returns:
        True if the date is a market holiday
    """
    year = check_date.year

    # Determine which holiday file to use
    if year == 2025 or year == 2026:
        year_range = "2025_2026"
    else:
        # For years outside our data, return False
        return False

    holidays = load_holidays(year_range)
    return check_date.date() in holidays