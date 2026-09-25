"""
Unit tests for writer.py (Bloom filter, StreamDeduplicator, and write_stream).
"""

from pathlib import Path

from wordlist_gen.writer import BloomFilter, StreamDeduplicator, write_stream


def test_bloom_filter_basic():
    bf = BloomFilter(size_bytes=1024, num_hashes=3)
    assert not bf.add("apple")
    assert bf.add("apple")
    assert not bf.add("banana")
    assert bf.add("banana")


def test_stream_deduplicator_window():
    dedup = StreamDeduplicator(mode="window", window_size=5)
    items = ["a", "b", "a", "c", "b", "d"]
    # "a" appears again within window of 5 -> dropped
    result = list(dedup.deduplicate(items))
    assert result == ["a", "b", "c", "d"]
    assert dedup.duplicates_dropped == 2


def test_stream_deduplicator_exact():
    dedup = StreamDeduplicator(mode="exact")
    items = ["one", "two", "one", "three", "two"]
    result = list(dedup.deduplicate(items))
    assert result == ["one", "two", "three"]
    assert dedup.duplicates_dropped == 2


def test_write_stream_file(tmp_path: Path):
    out_file = tmp_path / "out.txt"
    items = ["pass1", "pass2", "pass3"]
    stats = write_stream(items, output_path=out_file)

    assert stats.written == 3
    assert out_file.read_text(encoding="utf-8") == "pass1\npass2\npass3\n"


def test_write_stream_dry_run(tmp_path: Path):
    out_file = tmp_path / "out.txt"
    items = ["pass1", "pass2", "pass3"]
    stats = write_stream(items, output_path=out_file, dry_run=True)

    assert stats.written == 3
    assert not out_file.exists()
