"""
Password policy filter: length bounds, character classes, and regex rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Pattern

_DIGIT_RE: Pattern[str] = re.compile(r"\d")
_UPPER_RE: Pattern[str] = re.compile(r"[A-Z]")
_LOWER_RE: Pattern[str] = re.compile(r"[a-z]")
_SYMBOL_RE: Pattern[str] = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\",./<>?`~\\|]")


@dataclass
class PasswordPolicy:
    """Password complexity and policy validation rule set."""

    min_length: int = 8
    max_length: int = 64
    require_digit: bool = False
    require_upper: bool = False
    require_lower: bool = False
    require_symbol: bool = False
    regex_filter: Optional[str] = None
    regex_exclude: Optional[str] = None

    def __post_init__(self) -> None:
        self._custom_pattern: Optional[Pattern[str]] = (
            re.compile(self.regex_filter) if self.regex_filter else None
        )
        self._exclude_pattern: Optional[Pattern[str]] = (
            re.compile(self.regex_exclude) if self.regex_exclude else None
        )

    def validate(self, password: str) -> bool:
        """
        Validate whether a candidate password conforms to this policy.
        Optimized with fast short-circuit order for maximum throughput.
        """
        # 1. Length bounds (fast O(1) integer checks)
        pwd_len = len(password)
        if pwd_len < self.min_length or pwd_len > self.max_length:
            return False

        # 2. Required character classes
        if self.require_digit and not _DIGIT_RE.search(password):
            return False

        if self.require_upper and not _UPPER_RE.search(password):
            return False

        if self.require_lower and not _LOWER_RE.search(password):
            return False

        if self.require_symbol and not _SYMBOL_RE.search(password):
            return False

        # 3. Custom regex pattern inclusion
        if self._custom_pattern and not self._custom_pattern.search(password):
            return False

        # 4. Custom regex pattern exclusion
        if self._exclude_pattern and self._exclude_pattern.search(password):
            return False

        return True


def filter_passwords(
    stream: Iterable[str], policy: Optional[PasswordPolicy] = None
) -> Iterator[str]:
    """
    Stream filter that yields only passwords conforming to the given policy.
    If policy is None, yields all non-empty passwords without modification.
    """
    if policy is None:
        for pwd in stream:
            if pwd:
                yield pwd
        return

    validate = policy.validate
    for pwd in stream:
        if pwd and validate(pwd):
            yield pwd
