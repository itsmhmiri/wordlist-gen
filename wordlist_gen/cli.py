"""
Command-line interface (CLI) for wordlist-gen.
Provides arguments, options, execution flow, and rich terminal output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:  # pragma: no cover
    Console = None  # type: ignore
    Panel = None  # type: ignore
    Table = None  # type: ignore

from wordlist_gen.filters import PasswordPolicy
from wordlist_gen.generator import WordlistConfig, generate_wordlist
from wordlist_gen.hasher import HashFormat
from wordlist_gen.mutators.leet_mutator import LeetLevel
from wordlist_gen.profile import TargetProfile, load_profile_from_file
from wordlist_gen.writer import write_stream


def build_parser() -> argparse.ArgumentParser:
    """Build and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="wordlist-gen",
        description="Targeted OSINT Wordlist & Password Pattern Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input Seeds
    parser.add_argument(
        "-p",
        "--profile",
        metavar="FILE",
        help="Path to JSON/YAML target profile file",
    )
    parser.add_argument(
        "-n",
        "--names",
        metavar="NAMES",
        help="Comma-separated target names (e.g. John,Doe,Johnny)",
    )
    parser.add_argument(
        "-o",
        "--org",
        metavar="ORG",
        help="Target organization name (e.g. AcmeCorp)",
    )
    parser.add_argument(
        "-k",
        "--keywords",
        metavar="KEYS",
        help="Comma-separated contextual keywords",
    )
    parser.add_argument(
        "-d",
        "--dates",
        metavar="DATES",
        help="Comma-separated years or dates (e.g. 1990,2024)",
    )

    # Mutation options
    parser.add_argument(
        "--leet",
        choices=["none", "light", "aggressive"],
        default="light",
        help="Leetspeak mutation aggressiveness (default: light)",
    )

    # Password Policy Filter
    parser.add_argument(
        "--min-len",
        type=int,
        default=8,
        metavar="MIN_LEN",
        help="Minimum password length filter (default: 8)",
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=32,
        metavar="MAX_LEN",
        help="Maximum password length filter (default: 32)",
    )
    parser.add_argument(
        "--require-digit",
        action="store_true",
        help="Enforce inclusion of at least one number [0-9]",
    )
    parser.add_argument(
        "--require-symbol",
        action="store_true",
        help="Enforce inclusion of at least one special character",
    )
    parser.add_argument(
        "--require-upper",
        action="store_true",
        help="Enforce inclusion of at least one uppercase letter",
    )
    parser.add_argument(
        "--require-lower",
        action="store_true",
        help="Enforce inclusion of at least one lowercase letter",
    )
    parser.add_argument(
        "--regex-filter",
        metavar="PATTERN",
        help="Regex pattern inclusion filter",
    )
    parser.add_argument(
        "--regex-exclude",
        metavar="PATTERN",
        help="Regex pattern exclusion filter",
    )

    # Hasher
    parser.add_argument(
        "--hash",
        choices=["plain", "md5", "sha1", "sha256", "ntlm"],
        default="plain",
        dest="hash_format",
        help="Output format: plaintext or precomputed hash (default: plain)",
    )
    parser.add_argument(
        "--include-plain",
        action="store_true",
        help="Output in <plaintext>:<hash> format when hashing",
    )
    parser.add_argument(
        "--reverse-pair",
        action="store_true",
        help="Output in <hash>:<plaintext> format when hashing with --include-plain",
    )

    # Output & Execution
    parser.add_argument(
        "-out",
        "--output",
        metavar="FILE",
        dest="output_file",
        help="Destination output file (default: stdout)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate estimated dictionary count without writing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print real-time generation metrics",
    )

    return parser


def parse_comma_separated(value: Optional[str]) -> List[str]:
    """Split comma-separated CLI arguments into clean string tokens."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def print_rich_summary(
    stats,
    config: WordlistConfig,
    output_file: Optional[str],
    dry_run: bool,
) -> None:
    """Print an aesthetic summary table using Rich (to stderr to preserve stdout pipelines)."""
    if Console is None or Table is None:  # pragma: no cover
        err_msg = (
            f"[wordlist-gen] Generated {stats.written:,} candidates in "
            f"{stats.elapsed_seconds:.2f}s ({stats.rate_per_second:,.0f} words/s)\n"
        )
        sys.stderr.write(err_msg)
        return

    console = Console(stderr=True)
    table = Table(title="Targeted Wordlist Generator - Run Summary", show_header=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Configuration", style="magenta")

    base_tokens = config.profile.get_all_base_tokens()
    table.add_row("Base Seed Tokens", f"{len(base_tokens)} tokens ({', '.join(base_tokens[:6])}{'...' if len(base_tokens) > 6 else ''})")
    table.add_row("Date Seeds", f"{len(config.profile.dates)} dates ({', '.join(config.profile.dates)})")
    table.add_row("Leetspeak Level", config.leet_level.value)

    if config.policy:
        rules = [f"len={config.policy.min_length}..{config.policy.max_length}"]
        if config.policy.require_digit:
            rules.append("digit")
        if config.policy.require_upper:
            rules.append("upper")
        if config.policy.require_symbol:
            rules.append("symbol")
        table.add_row("Policy Filter", ", ".join(rules))
    else:
        table.add_row("Policy Filter", "None")

    table.add_row("Hash Format", config.hash_format.value)
    dest = "stdout" if not output_file else output_file
    if dry_run:
        dest += " (dry-run, no output written)"
    table.add_row("Destination", dest)
    table.add_row("Total Output", f"{stats.written:,} candidates")
    table.add_row("Elapsed Time", f"{stats.elapsed_seconds:.3f} seconds")
    table.add_row("Throughput", f"{stats.rate_per_second:,.0f} candidates/sec")

    console.print(table)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. Load or initialize profile
    if args.profile:
        try:
            profile = load_profile_from_file(args.profile)
        except Exception as e:
            sys.stderr.write(f"Error loading profile '{args.profile}': {e}\n")
            return 1
    else:
        profile = TargetProfile()

    # 2. Merge CLI seed arguments
    names = parse_comma_separated(args.names)
    keywords = parse_comma_separated(args.keywords)
    dates = parse_comma_separated(args.dates)
    profile.merge_cli_args(
        names=names,
        org=args.org,
        keywords=keywords,
        dates=dates,
    )

    # Verify that at least one seed or date was supplied
    if not profile.get_all_base_tokens() and not profile.dates:
        sys.stderr.write(
            "Error: No seed inputs provided. Specify --profile or seed flags (-n, -o, -k, -d).\n"
            "Run 'wordlist-gen --help' for usage.\n"
        )
        return 1

    # 3. Build Password Policy
    policy = PasswordPolicy(
        min_length=args.min_len,
        max_length=args.max_len,
        require_digit=args.require_digit,
        require_upper=args.require_upper,
        require_lower=args.require_lower,
        require_symbol=args.require_symbol,
        regex_filter=args.regex_filter,
        regex_exclude=args.regex_exclude,
    )

    # 4. Build Configuration
    config = WordlistConfig(
        profile=profile,
        leet_level=LeetLevel(args.leet),
        policy=policy,
        hash_format=HashFormat(args.hash_format),
        include_plain=args.include_plain,
        reverse_pair=args.reverse_pair,
    )

    # 5. Execute streaming pipeline
    stream = generate_wordlist(config)

    # 6. Write output
    try:
        stats = write_stream(
            stream=stream,
            output_path=args.output_file,
            dry_run=args.dry_run,
        )
    except (BrokenPipeError, KeyboardInterrupt):  # pragma: no cover
        # Graceful exit for piping to tools like head/grep
        sys.stderr.close()
        return 0

    # 7. Print metrics if requested
    if args.verbose or args.dry_run:
        print_rich_summary(stats, config, args.output_file, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
