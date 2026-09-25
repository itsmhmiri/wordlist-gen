"""
End-to-end integration tests and verification for wordlist_gen.
Covers all four verification tests from Specification Section 9.
"""

import json
import re
import tracemalloc
from pathlib import Path

from wordlist_gen.cli import main
from wordlist_gen.filters import PasswordPolicy
from wordlist_gen.generator import WordlistConfig, generate_wordlist
from wordlist_gen.hasher import HashFormat, ntlm_hash
from wordlist_gen.mutators.leet_mutator import LeetLevel
from wordlist_gen.profile import TargetInfo, TargetProfile


# --- Verification Test 1: Leetspeak Mutation Completeness ---
def test_verification_1_leet_completeness():
    """
    Test 1 (Leetspeak Mutation Completeness):
    Input 'test' with --leet light. Verify outputs contain t3st, test,
    and permutations with upper/lower variants.
    """
    profile = TargetProfile(
        target=TargetInfo(first_name="test"),
    )
    config = WordlistConfig(
        profile=profile,
        leet_level=LeetLevel.LIGHT,
        policy=PasswordPolicy(min_length=1, max_length=64),
    )
    words = set(generate_wordlist(config))

    # Core base variants
    assert "test" in words
    assert "t3st" in words
    # Case variants
    assert "Test" in words
    assert "T3st" in words
    assert "TEST" in words
    assert "T3ST" in words


# --- Verification Test 2: NTLM Hash Correctness ---
def test_verification_2_ntlm_correctness(tmp_path: Path):
    """
    Test 2 (NTLM Hash Correctness):
    Validate known test vectors:
    'admin' -> ntlm: 209c6174da490caeb422f3fa5a7ae634
    'password' -> ntlm: 8846f7eaee8fb117ad06bdd830b7586c
    """
    assert ntlm_hash("admin") == "209c6174da490caeb422f3fa5a7ae634"
    assert ntlm_hash("password") == "8846f7eaee8fb117ad06bdd830b7586c"

    # Verify via CLI hashing pipeline
    out_file = tmp_path / "hashes.txt"
    code = main([
        "-n", "admin",
        "--leet", "none",
        "--min-len", "1",
        "--hash", "ntlm",
        "-out", str(out_file),
    ])
    assert code == 0
    lines = out_file.read_text(encoding="utf-8").splitlines()
    assert "209c6174da490caeb422f3fa5a7ae634" in lines


# --- Verification Test 3: Policy Filter Enforcement ---
def test_verification_3_policy_filter_enforcement():
    r"""
    Test 3 (Policy Filter Enforcement):
    Generate candidates with --min-len 8 --require-digit --require-symbol.
    Assert that 100% of generated lines satisfy:
    len(pw) >= 8, re.search(r"\d", pw), and re.search(r"\W", pw) or symbol class.
    """
    profile = TargetProfile(
        target=TargetInfo(first_name="John", organization="AcmeCorp"),
        dates=["2024"],
        keywords=["admin", "secret"],
    )
    policy = PasswordPolicy(
        min_length=8,
        max_length=64,
        require_digit=True,
        require_symbol=True,
    )
    config = WordlistConfig(
        profile=profile,
        leet_level=LeetLevel.LIGHT,
        policy=policy,
    )

    count = 0
    symbol_pattern = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\",./<>?`~\\|]")
    for word in generate_wordlist(config):
        count += 1
        assert len(word) >= 8, f"Word '{word}' violates min length"
        assert re.search(r"\d", word), f"Word '{word}' missing digit"
        assert symbol_pattern.search(word), f"Word '{word}' missing symbol"
        if count >= 1000:
            break

    assert count > 0, "Should have generated matching candidates"


# --- Verification Test 4: Memory Bound Check (< 50 MB) ---
def test_verification_4_memory_bound_check():
    """
    Test 4 (Memory Bound Check):
    Run generator producing over 1,000,000 lines. Monitor process memory
    using tracemalloc to ensure resident memory stays strictly under 50 MB.
    """
    tracemalloc.start()

    profile = TargetProfile(
        target=TargetInfo(
            first_name="Alexander",
            last_name="Montgomery",
            organization="CyberSecuritySystems",
        ),
        dates=["1985", "1990", "2020", "2024"],
        keywords=["administrator", "supersecret", "enterprise", "rootaccess"],
    )
    config = WordlistConfig(
        profile=profile,
        leet_level=LeetLevel.AGGRESSIVE,
        policy=None,
        dedup_mode="window",
        window_size=100000,
    )

    generated = 0
    target_count = 1_000_000

    for _ in generate_wordlist(config):
        generated += 1
        if generated >= target_count:
            break

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    assert generated >= target_count
    # Strict specification assertion: memory must consume < 50 MB
    assert peak_mb < 50.0, f"Peak memory {peak_mb:.2f} MB exceeded 50 MB limit!"


# --- CLI Integration Tests ---
def test_cli_dry_run():
    code = main(["-n", "Alice", "-o", "Initech", "--dry-run", "-v"])
    assert code == 0


def test_cli_profile_file(tmp_path: Path):
    profile_path = tmp_path / "profile.json"
    profile_data = {
        "target": {"first_name": "Bob", "organization": "Globex"},
        "dates": ["2023"],
    }
    profile_path.write_text(json.dumps(profile_data), encoding="utf-8")
    out_file = tmp_path / "wordlist.txt"

    code = main([
        "-p", str(profile_path),
        "-out", str(out_file),
        "--min-len", "4",
    ])
    assert code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Bob" in content or "Globex" in content


def test_cli_no_seeds_error(capsys):
    code = main([])
    assert code == 1


def test_cli_hash_include_plain(tmp_path: Path):
    out_file = tmp_path / "hashes.txt"
    code = main([
        "-n", "root",
        "--leet", "none",
        "--min-len", "1",
        "--hash", "md5",
        "--include-plain",
        "-out", str(out_file),
    ])
    assert code == 0
    lines = out_file.read_text(encoding="utf-8").splitlines()
    assert any(":" in line and "root" in line for line in lines)
