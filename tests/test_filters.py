"""
Unit tests for filters.py (password policy and regex validation).
"""

from wordlist_gen.filters import PasswordPolicy, filter_passwords


def test_password_policy_length_bounds():
    policy = PasswordPolicy(min_length=8, max_length=12)
    assert not policy.validate("short")  # 5 chars
    assert policy.validate("validlen1")  # 9 chars
    assert policy.validate("twelvechars!")  # 12 chars
    assert not policy.validate("thispasswordistoolong")  # 21 chars


def test_password_policy_require_digit():
    policy = PasswordPolicy(min_length=4, require_digit=True)
    assert not policy.validate("Password")
    assert policy.validate("Password1")
    assert policy.validate("12345")


def test_password_policy_require_upper_and_lower():
    policy = PasswordPolicy(min_length=4, require_upper=True, require_lower=True)
    assert not policy.validate("password")
    assert not policy.validate("PASSWORD")
    assert policy.validate("PassWord")


def test_password_policy_require_symbol():
    policy = PasswordPolicy(min_length=4, require_symbol=True)
    assert not policy.validate("Password123")
    assert policy.validate("Password123!")
    assert policy.validate("Pass_word")
    assert policy.validate("Pass#word")


def test_password_policy_regex_rules():
    policy = PasswordPolicy(
        min_length=4,
        regex_filter=r"^Acme",
        regex_exclude=r"test",
    )
    assert policy.validate("AcmeCorp2024")
    assert not policy.validate("BetaCorp2024")
    assert not policy.validate("AcmeCorp_test")


def test_filter_passwords_stream():
    policy = PasswordPolicy(min_length=8, require_digit=True, require_symbol=True)
    inputs = [
        "short",
        "ValidPass1!",
        "NoDigit!",
        "NoSymbol123",
        "AnotherGood1#",
    ]
    results = list(filter_passwords(inputs, policy))
    assert results == ["ValidPass1!", "AnotherGood1#"]


def test_filter_passwords_none_policy():
    inputs = ["foo", "bar", ""]
    assert list(filter_passwords(inputs, None)) == ["foo", "bar"]
