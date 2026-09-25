"""
Streaming pipeline orchestrator for targeted wordlist generation.
Zero-buffer streaming pipeline:
Seed -> Case -> Affix/Delimiter -> Leet -> Filter -> Deduplicator -> Hasher
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from wordlist_gen.filters import PasswordPolicy, filter_passwords
from wordlist_gen.hasher import HashFormat, stream_hasher
from wordlist_gen.mutators.affix_mutator import generate_affix_mutations
from wordlist_gen.mutators.case_mutator import generate_case_mutations
from wordlist_gen.mutators.date_mutator import (
    generate_date_variations,
    generate_seasonal_tokens,
)
from wordlist_gen.mutators.leet_mutator import LeetLevel, generate_leet_mutations
from wordlist_gen.profile import TargetProfile
from wordlist_gen.writer import StreamDeduplicator


@dataclass
class WordlistConfig:
    """Configuration options for the wordlist generation pipeline."""

    profile: TargetProfile = field(default_factory=TargetProfile)
    leet_level: LeetLevel = LeetLevel.LIGHT
    policy: Optional[PasswordPolicy] = None
    hash_format: HashFormat = HashFormat.PLAIN
    include_plain: bool = False
    reverse_pair: bool = False
    dedup_mode: str = "window"
    window_size: int = 150000


def _generate_affix_stream(profile: TargetProfile) -> Iterator[str]:
    """
    Stream base seed tokens through case mutations, date variations,
    and affix/delimiter combinations.
    """
    base_tokens = profile.get_all_base_tokens()
    if not base_tokens and not profile.dates:
        return

    # Expand case mutations for each base token
    case_expanded_tokens: List[str] = []
    for token in base_tokens:
        for variant in generate_case_mutations(token):
            case_expanded_tokens.append(variant)

    # Date variations & seasonal tokens
    date_tokens: List[str] = list(generate_date_variations(profile.dates))
    seasonal_tokens = list(generate_seasonal_tokens(profile.dates))
    all_tokens = case_expanded_tokens + seasonal_tokens

    # Generate affix, delimiter, and pair combinations
    yield from generate_affix_mutations(
        tokens=all_tokens,
        dates=date_tokens,
        custom_symbols=profile.custom_symbols,
    )


def _generate_leet_stream(
    stream: Iterator[str], leet_level: LeetLevel | str
) -> Iterator[str]:
    """Stream candidates through leetspeak recursive cartesian products."""
    level = LeetLevel(leet_level) if isinstance(leet_level, str) else leet_level
    if level == LeetLevel.NONE:
        yield from stream
        return

    for word in stream:
        yield from generate_leet_mutations(word, level=level)


def generate_wordlist(config: WordlistConfig) -> Iterator[str]:
    """
    End-to-end streaming pipeline generator.
    Yields password candidates one-by-one with zero list accumulation.
    """
    # 1. Base tokens & affixes
    affix_stream = _generate_affix_stream(config.profile)

    # 2. Leetspeak mutations
    leet_stream = _generate_leet_stream(affix_stream, config.leet_level)

    # 3. Password policy filtering
    filtered_stream = filter_passwords(leet_stream, config.policy)

    # 4. Stream deduplication (memory-bounded window/bloom)
    deduplicator = StreamDeduplicator(
        mode=config.dedup_mode,
        window_size=config.window_size,
    )
    deduped_stream = deduplicator.deduplicate(filtered_stream)

    # 5. Cryptographic hash output formatting
    yield from stream_hasher(
        deduped_stream,
        hash_format=config.hash_format,
        include_plain=config.include_plain,
        reverse_pair=config.reverse_pair,
    )
