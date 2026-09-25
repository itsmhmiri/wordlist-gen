"""
Date & year expansion mutator: 4-digit years, 2-digit years, MMDD patterns, seasons.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Iterator, List, Set

SEASONS = ["Spring", "Summer", "Autumn", "Fall", "Winter"]


def generate_date_variations(dates: Iterable[str]) -> Iterator[str]:
    """
    Given a collection of date strings (e.g., '1988', '2024', '0512'),
    yield expanded date tokens:
    - 4-digit year: '1988' -> '1988', '88', "'88"
    - 2-digit year: '88' -> '88', "'88", '1988', '2088'
    - Month-Day: '0512' -> '0512', '512', '1205', '125'
    """
    seen: Set[str] = set()

    for d in dates:
        d_str = str(d).strip()
        if not d_str:
            continue

        candidates: List[str] = [d_str]

        # Check if 4-digit string (year or MMDD)
        if len(d_str) == 4 and d_str.isdigit():
            two_digit = d_str[2:]
            candidates.extend([two_digit, f"'{two_digit}"])

            # Check if valid MMDD (or DDMM)
            mm_val = int(d_str[:2])
            dd_val = int(d_str[2:])
            if 1 <= mm_val <= 12 and 1 <= dd_val <= 31:
                mm = d_str[:2]
                dd = d_str[2:]
                candidates.extend([
                    f"{mm_val}{dd}",
                    f"{mm_val}{dd_val}",
                    f"{dd}{mm}",
                    f"{dd_val}{mm_val}",
                ])

        # Check if 2-digit year
        elif len(d_str) == 2 and d_str.isdigit():
            candidates.extend([f"'{d_str}", f"20{d_str}", f"19{d_str}"])

        for c in candidates:
            if c not in seen:
                seen.add(c)
                yield c


def generate_seasonal_tokens(years: Iterable[str]) -> Iterator[str]:
    """
    Generate seasonal combinations (e.g. Spring2024, Summer24, Winter2025).
    """
    seen: Set[str] = set()
    expanded_years: List[str] = []

    for y in years:
        y_str = str(y).strip()
        if y_str.isdigit() and len(y_str) == 4:
            expanded_years.extend([y_str, y_str[2:]])
        elif y_str.isdigit() and len(y_str) == 2:
            expanded_years.extend([f"20{y_str}", y_str])

    # If no years provided, use current year and previous/next
    if not expanded_years:
        current_year = datetime.now().year
        for yr in (current_year - 1, current_year, current_year + 1):
            s_yr = str(yr)
            expanded_years.extend([s_yr, s_yr[2:]])

    for season in SEASONS:
        season_variants = [season, season.lower(), season.upper()]
        for sv in season_variants:
            for yr in expanded_years:
                token = f"{sv}{yr}"
                if token not in seen:
                    seen.add(token)
                    yield token
