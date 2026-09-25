"""
Streaming file writer, deduplication pipeline, and generation metrics.
Designed to process millions of candidates with < 50 MB memory consumption.
"""

from __future__ import annotations

import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Iterable, Iterator, Optional, Set, TextIO


class BloomFilter:
    """
    Fixed-memory Bloom filter for probabilistic stream deduplication.
    Uses double hashing over a preallocated bytearray.
    """

    def __init__(self, size_bytes: int = 16 * 1024 * 1024, num_hashes: int = 4) -> None:
        self.num_bits = size_bytes * 8
        self.num_hashes = num_hashes
        self.bit_array = bytearray(size_bytes)

    def _get_hashes(self, item: str) -> list[int]:
        # FNV-1a hash base
        h1 = 0x811C9DC5
        for byte in item.encode("utf-8"):
            h1 = ((h1 ^ byte) * 0x01000193) & 0xFFFFFFFF

        # Secondary hash (djb2)
        h2 = 5381
        for byte in item.encode("utf-8"):
            h2 = (((h2 << 5) + h2) + byte) & 0xFFFFFFFF

        return [(h1 + i * h2) % self.num_bits for i in range(self.num_hashes)]

    def add(self, item: str) -> bool:
        """
        Add item to filter. Returns True if item was already probably present,
        False if definitely not present before.
        """
        hashes = self._get_hashes(item)
        already_present = True
        for bit_index in hashes:
            byte_idx = bit_index >> 3
            bit_mask = 1 << (bit_index & 7)
            if not (self.bit_array[byte_idx] & bit_mask):
                already_present = False
                self.bit_array[byte_idx] |= bit_mask
        return already_present


class StreamDeduplicator:
    """
    Memory-bounded stream deduplicator.
    Supports 'window' (LRU sliding window) and 'bloom' filter modes.
    """

    def __init__(
        self,
        mode: str = "window",
        window_size: int = 150000,
        bloom_size_mb: int = 16,
    ) -> None:
        self.mode = mode.lower()
        self.window_size = window_size
        self._seen_set: Set[str] = set()
        self._window: Deque[str] = deque()
        self._bloom: Optional[BloomFilter] = (
            BloomFilter(size_bytes=bloom_size_mb * 1024 * 1024)
            if self.mode == "bloom"
            else None
        )
        self.duplicates_dropped: int = 0

    def is_duplicate(self, item: str) -> bool:
        """Check if an item is a duplicate and record its presence."""
        if self.mode == "bloom" and self._bloom is not None:
            is_dup = self._bloom.add(item)
            if is_dup:
                self.duplicates_dropped += 1
            return is_dup

        if self.mode == "exact":
            if item in self._seen_set:
                self.duplicates_dropped += 1
                return True
            self._seen_set.add(item)
            return False

        # Default: sliding window
        if item in self._seen_set:
            self.duplicates_dropped += 1
            return True

        self._seen_set.add(item)
        self._window.append(item)
        if len(self._window) > self.window_size:
            oldest = self._window.popleft()
            self._seen_set.remove(oldest)

        return False

    def deduplicate(self, stream: Iterable[str]) -> Iterator[str]:
        """Stream filter that yields only non-duplicate items."""
        for item in stream:
            if not self.is_duplicate(item):
                yield item


@dataclass
class GenerationStats:
    """Statistics collected during wordlist generation."""

    written: int = 0
    duplicates_dropped: int = 0
    elapsed_seconds: float = 0.0

    @property
    def rate_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0
        return self.written / self.elapsed_seconds


def write_stream(
    stream: Iterable[str],
    output_path: Optional[str | Path] = None,
    dry_run: bool = False,
    buffer_size: int = 65536,
) -> GenerationStats:
    """
    Consume the generator stream, writing line-by-line to output_path or stdout.
    In dry_run mode, counts the candidates without writing to disk or terminal.
    """
    stats = GenerationStats()
    start_time = time.perf_counter()

    if dry_run:
        for _ in stream:
            stats.written += 1
        stats.elapsed_seconds = time.perf_counter() - start_time
        return stats

    out_file: TextIO
    close_file = False

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        out_file = path.open("w", buffering=buffer_size, encoding="utf-8")
        close_file = True
    else:
        out_file = sys.stdout

    try:
        for word in stream:
            out_file.write(word)
            out_file.write("\n")
            stats.written += 1
    finally:
        if close_file:
            out_file.close()
        else:
            out_file.flush()

    stats.elapsed_seconds = time.perf_counter() - start_time
    return stats
