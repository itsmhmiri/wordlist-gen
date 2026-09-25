"""
Case mutation engine: lower, upper, title, toggle, alternate.
"""

from __future__ import annotations

from typing import Iterator, Set


def generate_case_mutations(word: str) -> Iterator[str]:
    """
    Yield unique case mutations of a given word:
    - original
    - lower
    - upper
    - title / capitalized
    - swapcase / inverted
    - inverted title (lower first letter, uppercase remainder)
    - alternating cases (starting with upper or lower)
    """
    if not word:
        return

    seen: Set[str] = set()

    def _yield(candidate: str) -> Iterator[str]:
        if candidate and candidate not in seen:
            seen.add(candidate)
            yield candidate

    # 1. Original
    yield from _yield(word)

    # 2. Lowercase
    yield from _yield(word.lower())

    # 3. Uppercase
    yield from _yield(word.upper())

    # 4. Title / Capitalize
    yield from _yield(word.capitalize())
    yield from _yield(word.title())

    # 5. Swapcase / Invert
    yield from _yield(word.swapcase())

    # 6. Inverted title: e.g. "aCME" or "pASSWORD"
    if len(word) > 1:
        yield from _yield(word[0].lower() + word[1:].upper())

    # 7. Alternating cases
    alt_upper = "".join(
        c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(word)
    )
    yield from _yield(alt_upper)

    alt_lower = "".join(
        c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(word)
    )
    yield from _yield(alt_lower)
