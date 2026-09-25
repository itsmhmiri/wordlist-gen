# wordlist-gen 🎯

A smart, fast CLI tool that builds targeted password wordlists from OSINT info.

Instead of generating gigabytes of random gibberish like `crunch` does (nobody's password is `qxzjk9`), **wordlist-gen** models how real humans actually create passwords: names, pets, company names, seasons, years, and common leetspeak substitutions (like `Acme2024!`, `B!ddy#99`, or `Winter2023`).

Feed it a few seeds—from CLI flags or a YAML profile—and get a tailored, policy-compliant dictionary ready for your penetration test or security audit.

![wordlist-gen demo](assets/demo2.gif)

---

## 💡 Why use this?

Most password audits waste time running general wordlists like RockYou or brute-forcing every character combination. But during an authorized engagement, you usually know something about your target:
- The company name and department
- Target employee names or nicknames
- Pet names, family names, or hobbies
- Relevant years or dates

`wordlist-gen` takes those small pieces of intelligence and turns them into realistic, high-probability password candidates in fractions of a second—without eating up all your RAM.

---

## ✨ Features

- **OSINT-Driven Seed Tokens**: Accepts names, organizations, departments, keywords, and dates. Automatically handles first/last compound variations (e.g., `JohnDoe`, `JDoe`, `JohnD`).
- **Human Password Modeling**:
  - **Case variations**: lowercase, UPPERCASE, TitleCase, and toggle.
  - **Affixes & Delimiters**: Smart prefixes, suffixes, and separators (`.`, `_`, `-`, `!`, `@`, `#`, etc.).
  - **Date & Season logic**: Expands 4-digit years into 2-digit years, seasons (`Summer2024`), and common date patterns.
  - **Configurable Leetspeak**: `none`, `light` (`e` → `3`, `a` → `@`), or `aggressive` substitutions.
- **Password Policy Filtering**: Only keep candidates that match the target's actual password policy (`--min-len`, `--max-len`, `--require-digit`, `--require-symbol`, `--require-upper`, or custom regex).
- **On-the-Fly Hashing**: Generate plaintext or precomputed hashes (`md5`, `sha1`, `sha256`, `ntlm`), with optional `<plain>:<hash>` mapping.
- **Zero-Buffer Streaming**: Everything streams line-by-line with bounded-memory deduplication. Generates >500k words/sec with almost zero RAM usage.
- **Pipe-Friendly**: Outputs clean passwords to stdout and logs/tables to stderr, so you can pipe straight into `hashcat`, `john`, or `head`.

---

## 🛠️ Tech Stack

We kept it lightweight, modern, and dependency-minimal:

- **Python 3.10+**: Core language runtime.
- **[Rich](https://github.com/Textualize/rich)**: For terminal summaries and clean metrics.
- **[PyYAML](https://pyyaml.org/)**: For parsing target profile YAML files.
- **Standard Library**: Built heavily on Python's native `hashlib`, `itertools`, `dataclasses`, and `argparse` for maximum speed and portability.
- **pytest**: Comprehensive test suite.

---

## 🚀 Getting Started

### 1. Clone & Set Up

```bash
git clone https://github.com/itsmhmiri/wordlist-gen.git
cd wordlist-gen

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode
pip install -e .
```

*(Optional) If you plan to run tests:*
```bash
pip install -e ".[dev]"
pytest
```

---

## 📖 How to Use

### 1. Quick One-Liner (CLI Flags)

The fastest way is providing target seeds right in your terminal:

```bash
# Generate passwords for John at AcmeCorp with 2024 dates, enforcing standard corporate policy
wordlist-gen -n John,Doe -o Acme -d 2024 --require-digit --require-symbol -out wordlist.txt
```

### 2. Preview Without Writing (`--dry-run`)

Want to see how many candidates it would generate and how fast without creating a massive file?

```bash
wordlist-gen -n John -o Acme -d 2024 --dry-run
```

This prints a quick summary table with candidate count and generation speed.

### 3. Using a Target Profile (`profile.yaml`)

For deeper OSINT engagements, create a YAML profile for your target:

```yaml
# target.yaml
target:
  first_name: John
  last_name: Doe
  nickname: Johnny
  organization: AcmeCorp
  department: SecOps
  pet_name: Buddy

dates:
  - 2023
  - 2024

keywords:
  - devops
  - admin
  - security
```

Run the generator with the profile:

```bash
wordlist-gen -p target.yaml --leet light --min-len 8 --require-digit -out target_wordlist.txt -v
```

### 4. Direct Hashing (NTLM, SHA-256, MD5)

If you're comparing against a dump or offline hash list, generate hashes directly:

```bash
# Output NTLM hashes
wordlist-gen -n John -o Acme -d 2024 --hash ntlm -out ntlm_candidates.txt

# Output formatted as plaintext:hash for lookup tables
wordlist-gen -n John -o Acme -d 2024 --hash sha256 --include-plain
```

### 5. Piping into Hashcat or John

Because `wordlist-gen` writes passwords to `stdout` and status info to `stderr`, you can stream candidates directly into cracking tools without touching the disk:

```bash
wordlist-gen -p target.yaml --leet light | hashcat -m 1000 hashes.txt
```

---

## ⚙️ CLI Options Reference

| Option | Description | Default |
|---|---|---|
| `-p, --profile FILE` | Path to JSON or YAML target profile | None |
| `-n, --names NAMES` | Target names / nicknames (`John,Doe,Johnny`) | None |
| `-o, --org ORG` | Target organization (`AcmeCorp`) | None |
| `-k, --keywords KEYS` | Extra keywords (`admin,devops`) | None |
| `-d, --dates DATES` | Years or dates (`1990,2024`) | None |
| `--leet` | Leetspeak level: `none`, `light`, `aggressive` | `light` |
| `--min-len / --max-len` | Password length limits | `8` / `32` |
| `--require-digit` | Candidate must contain a number | Off |
| `--require-symbol` | Candidate must contain a symbol | Off |
| `--require-upper` | Candidate must contain an uppercase letter | Off |
| `--require-lower` | Candidate must contain a lowercase letter | Off |
| `--regex-filter PATTERN` | Must match regex pattern | None |
| `--regex-exclude PATTERN` | Exclude strings matching regex | None |
| `--hash FORMAT` | Hash format: `plain`, `md5`, `sha1`, `sha256`, `ntlm` | `plain` |
| `--include-plain` | Format output as `<plaintext>:<hash>` | Off |
| `--reverse-pair` | Format output as `<hash>:<plaintext>` | Off |
| `-out, --output FILE` | Output file path | stdout |
| `--dry-run` | Show estimated count without writing output | Off |
| `-v, --verbose` | Print run metrics and summary table to stderr | Off |

---

## ⚖️ Legal & Ethical Notice

This tool is created strictly for authorized security assessments, penetration testing, and educational research. Only use it against systems and accounts you have explicit permission to test.
