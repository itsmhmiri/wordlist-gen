"""
Leetspeak mutator: none, light, aggressive with recursive cartesian branching.
"""

from __future__ import annotations

import itertools
from enum import Enum
from typing import Dict, Iterator, List, Optional, Sequence, Set


class LeetLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    AGGRESSIVE = "aggressive"


LIGHT_LEET_MAP: Dict[str, List[str]] = {
    "a": ["a", "4", "@"],
    "A": ["A", "4", "@"],
    "e": ["e", "3"],
    "E": ["E", "3"],
    "i": ["i", "1", "!"],
    "I": ["I", "1", "!"],
    "o": ["o", "0"],
    "O": ["O", "0"],
}

AGGRESSIVE_LEET_MAP: Dict[str, List[str]] = {
    **LIGHT_LEET_MAP,
    "s": ["s", "$", "5"],
    "S": ["S", "$", "5"],
    "t": ["t", "7"],
    "T": ["T", "7"],
    "b": ["b", "8"],
    "B": ["B", "8"],
    "l": ["l", "1"],
    "L": ["L", "1"],
    "g": ["g", "9"],
    "G": ["G", "9"],
    "z": ["z", "2"],
    "Z": ["Z", "2"],
}


def get_leet_map(level: LeetLevel | str) -> Optional[Dict[str, List[str]]]:
    """Retrieve the leetspeak substitution map for the specified level."""
    lvl = LeetLevel(level) if isinstance(level, str) else level
    if lvl == LeetLevel.NONE:
        return None
    elif lvl == LeetLevel.LIGHT:
        return LIGHT_LEET_MAP
    elif lvl == LeetLevel.AGGRESSIVE:
        return AGGRESSIVE_LEET_MAP
    raise ValueError(f"Unknown leet level: {level}")


def generate_leet_mutations(
    word: str,
    level: LeetLevel | str = LeetLevel.LIGHT,
    max_permutations: int = 10000,
) -> Iterator[str]:
    """
    Yield all cartesian permutations of leetspeak replacements for a word.
    Uses itertools.product to stream results with O(1) memory overhead.
    """
    if not word:
        return

    mapping = get_leet_map(level)
    if mapping is None:
        yield word
        return

    # Build substitution choices per character
    char_choices: List[Sequence[str]] = []
    total_est = 1
    mutable_count = 0

    for char in word:
        replacements = mapping.get(char)
        if replacements:
            char_choices.append(replacements)
            total_est *= len(replacements)
            mutable_count += 1
        else:
            char_choices.append([char])

    # If no mutable characters, yield original word
    if mutable_count == 0:
        yield word
        return

    # If combinations are within limit, yield cartesian product directly
    seen: Set[str] = set()
    count = 0

    for combo in itertools.product(*char_choices):
        candidate = "".join(combo)
        if candidate not in seen:
            seen.add(candidate)
            yield candidate
            count += 1
            if count >= max_permutations:
                break
