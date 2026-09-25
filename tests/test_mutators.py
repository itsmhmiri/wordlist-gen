"""
Unit tests for mutation engines: case, date, affix, and leet.
"""

from wordlist_gen.mutators.affix_mutator import generate_affix_mutations
from wordlist_gen.mutators.case_mutator import generate_case_mutations
from wordlist_gen.mutators.date_mutator import (
    generate_date_variations,
    generate_seasonal_tokens,
)
from wordlist_gen.mutators.leet_mutator import (
    LeetLevel,
    generate_leet_mutations,
)


# --- Case Mutator Tests ---
def test_case_mutations():
    variants = list(generate_case_mutations("acmecorp"))
    assert "acmecorp" in variants
    assert "ACMECORP" in variants
    assert "Acmecorp" in variants
    assert "aCMECORP" in variants
    assert "AcMeCoRp" in variants
    assert "aCmEcOrP" in variants


def test_case_mutations_empty():
    assert list(generate_case_mutations("")) == []


# --- Date Mutator Tests ---
def test_date_variations_4digit():
    dates = ["1988", "2024"]
    variations = list(generate_date_variations(dates))
    assert "1988" in variations
    assert "88" in variations
    assert "'88" in variations
    assert "2024" in variations
    assert "24" in variations


def test_date_variations_2digit():
    variations = list(generate_date_variations(["99"]))
    assert "99" in variations
    assert "'99" in variations
    assert "1999" in variations


def test_date_variations_mmdd():
    variations = list(generate_date_variations(["0512"]))
    assert "0512" in variations
    assert "512" in variations
    assert "1205" in variations


def test_seasonal_tokens():
    tokens = list(generate_seasonal_tokens(["2024"]))
    assert "Spring2024" in tokens
    assert "spring2024" in tokens
    assert "Summer24" in tokens
    assert "Winter2024" in tokens


# --- Affix Mutator Tests ---
def test_affix_mutations_basic():
    mutations = list(
        generate_affix_mutations(
            tokens=["Admin"],
            dates=["2024"],
            custom_symbols=["!"],
        )
    )
    assert "Admin" in mutations
    assert "Admin!" in mutations
    assert "Admin123" in mutations
    assert "!Admin" in mutations
    assert "!Admin!" in mutations
    assert "Admin2024" in mutations
    assert "Admin_2024" in mutations
    assert "Admin2024!" in mutations
    assert "Admin_2024!" in mutations


def test_affix_mutations_pairs():
    mutations = list(
        generate_affix_mutations(
            tokens=["John", "Doe"],
            dates=["2024"],
        )
    )
    assert "JohnDoe" in mutations
    assert "John_Doe" in mutations
    assert "JohnDoe!" in mutations
    assert "John_Doe2024!" in mutations


def test_affix_mutations_empty():
    assert list(generate_affix_mutations([])) == []


# --- Leet Mutator Tests ---
def test_leet_none():
    results = list(generate_leet_mutations("password", level=LeetLevel.NONE))
    assert results == ["password"]


def test_leet_light_test_vector():
    # Specification Test 1: "test" with --leet light yields t3st, test
    results = set(generate_leet_mutations("test", level=LeetLevel.LIGHT))
    assert "test" in results
    assert "t3st" in results


def test_leet_light_password_permutations():
    # Specification requirement: recursive branching yields p4ssword, passw0rd, p4ssw0rd, p@ssw0rd
    results = set(generate_leet_mutations("password", level=LeetLevel.LIGHT))
    assert "password" in results
    assert "p4ssword" in results
    assert "passw0rd" in results
    assert "p4ssw0rd" in results
    assert "p@ssw0rd" in results


def test_leet_aggressive_symbols():
    # Aggressive includes s -> $, 5; t -> 7; b -> 8; l -> 1
    results = set(generate_leet_mutations("password", level=LeetLevel.AGGRESSIVE))
    assert "p@$$w0rd" in results
    assert "p455w0rd" in results


def test_leet_empty_and_no_mutable():
    assert list(generate_leet_mutations("")) == []
    assert list(generate_leet_mutations("xyz", level=LeetLevel.LIGHT)) == ["xyz"]


def test_leet_max_permutations_bound():
    # Long repetitive word should not hang or cause memory blowup
    results = list(
        generate_leet_mutations("aaaaaaaaaa", level=LeetLevel.LIGHT, max_permutations=50)
    )
    assert len(results) <= 50
