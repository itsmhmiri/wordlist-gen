"""
Affix & Delimiter mutator: prefix padding, suffix appending, delimiter insertion, word pairs.
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Optional, Sequence, Set

DEFAULT_PREFIXES: List[str] = ["!", "#", "@", "123", "The", "the", "."]
DEFAULT_SUFFIXES: List[str] = [
    "!",
    "!!",
    "!",
    "@",
    "#",
    "$",
    "123",
    "1234",
    "01",
    "1",
    "?",
    "*",
    "!@#",
]
DEFAULT_DELIMITERS: List[str] = ["", "_", ".", "-", "@", "!"]


def generate_affix_mutations(
    tokens: Sequence[str],
    dates: Optional[Iterable[str]] = None,
    custom_symbols: Optional[Sequence[str]] = None,
    prefixes: Optional[Sequence[str]] = None,
    suffixes: Optional[Sequence[str]] = None,
    delimiters: Optional[Sequence[str]] = None,
) -> Iterator[str]:
    """
    Generate affix and delimiter permutations for base tokens.
    Combinatorial patterns modeled on human password psychology:
    - {Seed}
    - {Seed}{Suffix}
    - {Prefix}{Seed}
    - {Prefix}{Seed}{Suffix}
    - {Seed}{Delimiter}{Date}
    - {Seed}{Date}{Suffix}
    - {Seed}{Delimiter}{Date}{Suffix}
    - {Seed1}{Delimiter}{Seed2}
    - {Seed1}{Seed2}{Suffix}
    - {Seed1}{Delimiter}{Seed2}{Date}{Suffix}
    """
    clean_tokens = [t.strip() for t in tokens if t and t.strip()]
    if not clean_tokens:
        return

    clean_dates = list(dates) if dates else []
    pfx_list = list(prefixes) if prefixes is not None else DEFAULT_PREFIXES
    sfx_list = list(suffixes) if suffixes is not None else list(DEFAULT_SUFFIXES)

    # Add custom symbols to suffixes and prefixes
    if custom_symbols:
        for sym in custom_symbols:
            if sym and sym not in sfx_list:
                sfx_list.append(sym)
            if sym and sym not in pfx_list:
                pfx_list.append(sym)

    delim_list = list(delimiters) if delimiters is not None else DEFAULT_DELIMITERS
    seen: Set[str] = set()

    def _yield(candidate: str) -> Iterator[str]:
        if candidate and candidate not in seen:
            seen.add(candidate)
            yield candidate

    # 1. Base tokens
    for token in clean_tokens:
        yield from _yield(token)

    # 2. Token + Suffix
    for token in clean_tokens:
        for sfx in sfx_list:
            yield from _yield(f"{token}{sfx}")

    # 3. Token + Delimiter + Suffix (when delimiter is non-empty)
    for token in clean_tokens:
        for delim in delim_list:
            if delim:
                for sfx in sfx_list:
                    yield from _yield(f"{token}{delim}{sfx}")

    # 4. Prefix + Token
    for token in clean_tokens:
        for pfx in pfx_list:
            yield from _yield(f"{pfx}{token}")
            for sfx in sfx_list:
                yield from _yield(f"{pfx}{token}{sfx}")

    # 5. Token + Date combinations
    for token in clean_tokens:
        for d in clean_dates:
            for delim in delim_list:
                yield from _yield(f"{token}{delim}{d}")
                for sfx in sfx_list:
                    yield from _yield(f"{token}{delim}{d}{sfx}")

    # 6. Compound pairs: Token1 + Token2 combinations (limited to first N tokens to prevent N^2 explosion)
    primary_tokens = clean_tokens[:15]
    for i, t1 in enumerate(primary_tokens):
        for j, t2 in enumerate(primary_tokens):
            if i != j:
                for delim in delim_list:
                    pair = f"{t1}{delim}{t2}"
                    yield from _yield(pair)
                    for sfx in sfx_list[:5]:
                        yield from _yield(f"{pair}{sfx}")
                    for d in clean_dates[:3]:
                        yield from _yield(f"{pair}{d}")
                        for sfx in sfx_list[:3]:
                            yield from _yield(f"{pair}{d}{sfx}")
