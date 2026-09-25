"""
Target profile schema, data model, and file loader (JSON/YAML).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


@dataclass
class TargetInfo:
    """Target persona and organizational metadata."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    pet_name: Optional[str] = None
    spouse_name: Optional[str] = None
    partner_name: Optional[str] = None
    child_names: List[str] = field(default_factory=list)
    other_names: List[str] = field(default_factory=list)

    def get_names(self) -> List[str]:
        """Extract all individual name tokens."""
        names: List[str] = []
        for val in (
            self.first_name,
            self.last_name,
            self.nickname,
            self.pet_name,
            self.spouse_name,
            self.partner_name,
        ):
            if val and val.strip():
                names.append(val.strip())

        for name in self.child_names + self.other_names:
            if name and name.strip():
                names.append(name.strip())

        # Also add compound names if first and last name both exist
        if self.first_name and self.last_name:
            f, l = self.first_name.strip(), self.last_name.strip()
            names.append(f"{f}{l}")
            names.append(f"{f[0]}{l}")
            names.append(f"{f}{l[0]}")

        # Unique preserving order
        seen = set()
        unique_names = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique_names.append(n)
        return unique_names

    def get_orgs(self) -> List[str]:
        """Extract organization and department tokens."""
        orgs: List[str] = []
        for val in (self.organization, self.department):
            if val and val.strip():
                cleaned = val.strip()
                if cleaned not in orgs:
                    orgs.append(cleaned)
        return orgs


@dataclass
class TargetProfile:
    """Complete OSINT profile configuration."""

    target: TargetInfo = field(default_factory=TargetInfo)
    dates: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    custom_symbols: List[str] = field(
        default_factory=lambda: ["!", "@", "#", "$", "%", "?", "*"]
    )

    def get_all_base_tokens(self) -> List[str]:
        """
        Extract all raw seed tokens across names, orgs, and keywords.
        Guarantees uniqueness while preserving logical prioritization.
        """
        tokens: List[str] = []
        tokens.extend(self.target.get_names())
        tokens.extend(self.target.get_orgs())
        for kw in self.keywords:
            if kw and kw.strip():
                tokens.append(kw.strip())

        # Deduplicate preserving order
        seen = set()
        unique_tokens = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                unique_tokens.append(t)
        return unique_tokens

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TargetProfile:
        """Construct a TargetProfile from a parsed dictionary."""
        target_data = data.get("target") or {}
        child_names_raw = target_data.get("child_names") or []
        if isinstance(child_names_raw, str):
            child_names = [c.strip() for c in child_names_raw.split(",") if c.strip()]
        elif isinstance(child_names_raw, list):
            child_names = [str(c).strip() for c in child_names_raw if str(c).strip()]
        else:
            child_names = []

        other_names_raw = target_data.get("other_names") or []
        if isinstance(other_names_raw, str):
            other_names = [c.strip() for c in other_names_raw.split(",") if c.strip()]
        elif isinstance(other_names_raw, list):
            other_names = [str(c).strip() for c in other_names_raw if str(c).strip()]
        else:
            other_names = []

        target = TargetInfo(
            first_name=target_data.get("first_name"),
            last_name=target_data.get("last_name"),
            nickname=target_data.get("nickname"),
            organization=target_data.get("organization"),
            department=target_data.get("department"),
            pet_name=target_data.get("pet_name"),
            spouse_name=target_data.get("spouse_name"),
            partner_name=target_data.get("partner_name"),
            child_names=child_names,
            other_names=other_names,
        )

        dates_raw = data.get("dates") or []
        if isinstance(dates_raw, str):
            dates = [d.strip() for d in dates_raw.split(",") if d.strip()]
        elif isinstance(dates_raw, list):
            dates = [str(d).strip() for d in dates_raw if str(d).strip()]
        else:
            dates = []

        keywords_raw = data.get("keywords") or []
        if isinstance(keywords_raw, str):
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        elif isinstance(keywords_raw, list):
            keywords = [str(k).strip() for k in keywords_raw if str(k).strip()]
        else:
            keywords = []

        symbols_raw = data.get("custom_symbols")
        if symbols_raw is not None:
            if isinstance(symbols_raw, list):
                custom_symbols = [str(s).strip() for s in symbols_raw if str(s).strip()]
            elif isinstance(symbols_raw, str):
                custom_symbols = [s for s in symbols_raw if not s.isspace()]
            else:
                custom_symbols = ["!", "@", "#", "$", "%", "?", "*"]
        else:
            custom_symbols = ["!", "@", "#", "$", "%", "?", "*"]

        return cls(
            target=target,
            dates=dates,
            keywords=keywords,
            custom_symbols=custom_symbols,
        )

    def merge_cli_args(
        self,
        names: Optional[Iterable[str]] = None,
        org: Optional[str] = None,
        keywords: Optional[Iterable[str]] = None,
        dates: Optional[Iterable[str]] = None,
    ) -> None:
        """Merge additional values provided via CLI flags."""
        if names:
            for name in names:
                clean_name = str(name).strip()
                if clean_name and clean_name not in self.target.other_names:
                    self.target.other_names.append(clean_name)

        if org:
            clean_org = org.strip()
            if clean_org:
                if not self.target.organization:
                    self.target.organization = clean_org
                elif clean_org not in self.keywords:
                    self.keywords.append(clean_org)

        if keywords:
            for kw in keywords:
                clean_kw = str(kw).strip()
                if clean_kw and clean_kw not in self.keywords:
                    self.keywords.append(clean_kw)

        if dates:
            for d in dates:
                clean_d = str(d).strip()
                if clean_d and clean_d not in self.dates:
                    self.dates.append(clean_d)


def load_profile_from_file(file_path: str | Path) -> TargetProfile:
    """
    Load and parse a TargetProfile from a JSON or YAML file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Target profile file not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    data: Any = None
    if suffix in (".yaml", ".yml"):
        if yaml is None:
            raise ImportError("PyYAML is required to parse YAML profile files.")
        data = yaml.safe_load(content)
    elif suffix == ".json":
        data = json.loads(content)
    else:
        # Fallback: attempt JSON first, then YAML
        try:
            data = json.loads(content)
        except Exception:
            if yaml is not None:
                data = yaml.safe_load(content)
            else:
                raise ValueError(
                    f"Unsupported profile format for '{file_path}'. Expected JSON or YAML."
                )

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid profile content in '{file_path}': root structure must be an object/dict."
        )

    return TargetProfile.from_dict(data)
