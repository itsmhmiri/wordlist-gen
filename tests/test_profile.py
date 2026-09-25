"""
Unit tests for profile.py.
"""

from pathlib import Path

import pytest
import yaml

from wordlist_gen.profile import (
    TargetInfo,
    TargetProfile,
    load_profile_from_file,
)


def test_target_info_names_and_compounds():
    info = TargetInfo(
        first_name="John",
        last_name="Doe",
        nickname="Johnny",
        pet_name="Buddy",
        spouse_name="Jane",
        child_names=["Sam", "Lily"],
    )
    names = info.get_names()

    assert "John" in names
    assert "Doe" in names
    assert "Johnny" in names
    assert "Buddy" in names
    assert "Jane" in names
    assert "Sam" in names
    assert "Lily" in names
    # Compound names
    assert "JohnDoe" in names
    assert "JDoe" in names
    assert "JohnD" in names


def test_target_info_orgs():
    info = TargetInfo(organization="AcmeCorp", department="SecOps")
    orgs = info.get_orgs()
    assert orgs == ["AcmeCorp", "SecOps"]


def test_target_profile_from_dict():
    raw = {
        "target": {
            "first_name": "John",
            "last_name": "Doe",
            "nickname": "Johnny",
            "organization": "AcmeCorp",
            "department": "SecOps",
            "pet_name": "Buddy",
            "spouse_name": "Jane",
            "partner_name": None,
            "child_names": ["Sam", "Lily"],
        },
        "dates": ["1988", "2023", "2024", "2025", "0512"],
        "keywords": [
            "admin",
            "root",
            "pass",
            "welcome",
            "winter",
            "summer",
            "security",
        ],
        "custom_symbols": ["!", "@", "#", "$", "%", "?", "*"],
    }
    profile = TargetProfile.from_dict(raw)
    assert profile.target.first_name == "John"
    assert profile.target.last_name == "Doe"
    assert profile.dates == ["1988", "2023", "2024", "2025", "0512"]
    assert "admin" in profile.keywords
    assert "!" in profile.custom_symbols

    tokens = profile.get_all_base_tokens()
    assert "John" in tokens
    assert "AcmeCorp" in tokens
    assert "admin" in tokens


def test_target_profile_merge_cli_args():
    profile = TargetProfile()
    profile.merge_cli_args(
        names=["Alice", "Bob"],
        org="CyberDyne",
        keywords=["secret", "vault"],
        dates=["1995", "2024"],
    )
    assert "Alice" in profile.target.other_names
    assert "Bob" in profile.target.other_names
    assert profile.target.organization == "CyberDyne"
    assert "secret" in profile.keywords
    assert "1995" in profile.dates


def test_load_profile_from_json(tmp_path: Path):
    json_path = tmp_path / "target.json"
    json_path.write_text(
        '{"target": {"first_name": "Alice", "organization": "Umbrella"}, "dates": ["2022"], "keywords": ["virus"]}',
        encoding="utf-8",
    )

    profile = load_profile_from_file(json_path)
    assert profile.target.first_name == "Alice"
    assert profile.target.organization == "Umbrella"
    assert profile.dates == ["2022"]
    assert profile.keywords == ["virus"]


def test_load_profile_from_yaml(tmp_path: Path):
    yaml_path = tmp_path / "target.yaml"
    data = {
        "target": {
            "first_name": "Bruce",
            "last_name": "Wayne",
            "organization": "WayneEnterprises",
        },
        "dates": ["1939"],
        "keywords": ["batman", "gotham"],
    }
    yaml_path.write_text(yaml.dump(data), encoding="utf-8")

    profile = load_profile_from_file(yaml_path)
    assert profile.target.first_name == "Bruce"
    assert profile.target.last_name == "Wayne"
    assert "WayneEnterprises" in profile.get_all_base_tokens()


def test_load_profile_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_profile_from_file("nonexistent_profile.json")


def test_load_profile_invalid_content(tmp_path: Path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="root structure must be an object/dict"):
        load_profile_from_file(bad_path)
