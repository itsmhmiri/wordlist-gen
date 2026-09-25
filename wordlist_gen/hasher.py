"""
Cryptographic hash output module: MD5, SHA-1, SHA-256, NTLM.
Provides standard OpenSSL hashing with an RFC 1320 pure-Python MD4 fallback
for systems where MD4 is disabled by OpenSSL 3.0+ security policies.
"""

from __future__ import annotations

import hashlib
import struct
from enum import Enum
from typing import Callable, Dict, Iterable, Iterator


class HashFormat(str, Enum):
    PLAIN = "plain"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    NTLM = "ntlm"


def _pure_python_md4(msg: bytes) -> bytes:
    """
    RFC 1320 MD4 message-digest algorithm implementation in pure Python.
    Used as a fallback when hashlib.new('md4') is disabled by OpenSSL.
    """
    def _f(x: int, y: int, z: int) -> int:
        return (x & y) | (~x & z)

    def _g(x: int, y: int, z: int) -> int:
        return (x & y) | (x & z) | (y & z)

    def _h(x: int, y: int, z: int) -> int:
        return x ^ y ^ z

    def _rotl(x: int, n: int) -> int:
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    orig_len_bits = (8 * len(msg)) & 0xFFFFFFFFFFFFFFFF
    msg = msg + b"\x80"
    msg = msg + b"\x00" * ((56 - len(msg) % 64) % 64)
    msg = msg + struct.pack("<Q", orig_len_bits)

    A = 0x67452301
    B = 0xEFCDAB89
    C = 0x98BADCFE
    D = 0x10325476

    for i in range(0, len(msg), 64):
        X = struct.unpack("<16I", msg[i : i + 64])
        AA, BB, CC, DD = A, B, C, D

        # Round 1
        for a, b, c, d, k, s in [
            (0, 1, 2, 3, 0, 3), (3, 0, 1, 2, 1, 7), (2, 3, 0, 1, 2, 11), (1, 2, 3, 0, 3, 19),
            (0, 1, 2, 3, 4, 3), (3, 0, 1, 2, 5, 7), (2, 3, 0, 1, 6, 11), (1, 2, 3, 0, 7, 19),
            (0, 1, 2, 3, 8, 3), (3, 0, 1, 2, 9, 7), (2, 3, 0, 1, 10, 11), (1, 2, 3, 0, 11, 19),
            (0, 1, 2, 3, 12, 3), (3, 0, 1, 2, 13, 7), (2, 3, 0, 1, 14, 11), (1, 2, 3, 0, 15, 19),
        ]:
            reg = [A, B, C, D]
            reg[a] = _rotl((reg[a] + _f(reg[b], reg[c], reg[d]) + X[k]) & 0xFFFFFFFF, s)
            A, B, C, D = reg

        # Round 2
        for a, b, c, d, k, s in [
            (0, 1, 2, 3, 0, 3), (3, 0, 1, 2, 4, 5), (2, 3, 0, 1, 8, 9), (1, 2, 3, 0, 12, 13),
            (0, 1, 2, 3, 1, 3), (3, 0, 1, 2, 5, 5), (2, 3, 0, 1, 9, 9), (1, 2, 3, 0, 13, 13),
            (0, 1, 2, 3, 2, 3), (3, 0, 1, 2, 6, 5), (2, 3, 0, 1, 10, 9), (1, 2, 3, 0, 14, 13),
            (0, 1, 2, 3, 3, 3), (3, 0, 1, 2, 7, 5), (2, 3, 0, 1, 11, 9), (1, 2, 3, 0, 15, 13),
        ]:
            reg = [A, B, C, D]
            reg[a] = _rotl((reg[a] + _g(reg[b], reg[c], reg[d]) + X[k] + 0x5A827999) & 0xFFFFFFFF, s)
            A, B, C, D = reg

        # Round 3
        for a, b, c, d, k, s in [
            (0, 1, 2, 3, 0, 3), (3, 0, 1, 2, 8, 9), (2, 3, 0, 1, 4, 11), (1, 2, 3, 0, 12, 15),
            (0, 1, 2, 3, 2, 3), (3, 0, 1, 2, 10, 9), (2, 3, 0, 1, 6, 11), (1, 2, 3, 0, 14, 15),
            (0, 1, 2, 3, 1, 3), (3, 0, 1, 2, 9, 9), (2, 3, 0, 1, 5, 11), (1, 2, 3, 0, 13, 15),
            (0, 1, 2, 3, 3, 3), (3, 0, 1, 2, 11, 9), (2, 3, 0, 1, 7, 11), (1, 2, 3, 0, 15, 15),
        ]:
            reg = [A, B, C, D]
            reg[a] = _rotl((reg[a] + _h(reg[b], reg[c], reg[d]) + X[k] + 0x6ED9EBA1) & 0xFFFFFFFF, s)
            A, B, C, D = reg

        A = (A + AA) & 0xFFFFFFFF
        B = (B + BB) & 0xFFFFFFFF
        C = (C + CC) & 0xFFFFFFFF
        D = (D + DD) & 0xFFFFFFFF

    return struct.pack("<4I", A, B, C, D)


def md5_hash(password: str) -> str:
    """Compute hexadecimal MD5 hash."""
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def sha1_hash(password: str) -> str:
    """Compute hexadecimal SHA-1 hash."""
    return hashlib.sha1(password.encode("utf-8")).hexdigest()


def sha256_hash(password: str) -> str:
    """Compute hexadecimal SHA-256 hash."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ntlm_hash(password: str) -> str:
    """
    Compute hexadecimal NTLM hash (MD4 of UTF-16LE encoded password).
    Falls back gracefully to pure Python MD4 if OpenSSL MD4 is unavailable.
    """
    encoded = password.encode("utf-16le")
    try:
        return hashlib.new("md4", encoded).hexdigest()
    except Exception:
        return _pure_python_md4(encoded).hex()


_HASH_FUNCS: Dict[HashFormat, Callable[[str], str]] = {
    HashFormat.MD5: md5_hash,
    HashFormat.SHA1: sha1_hash,
    HashFormat.SHA256: sha256_hash,
    HashFormat.NTLM: ntlm_hash,
}


def format_hash_entry(
    password: str,
    hash_format: HashFormat | str = HashFormat.PLAIN,
    include_plain: bool = False,
    reverse_pair: bool = False,
) -> str:
    """
    Format a password into plain or hashed output.
    Supports <hash>, <plain>:<hash>, or <hash>:<plain>.
    """
    fmt = HashFormat(hash_format) if isinstance(hash_format, str) else hash_format
    if fmt == HashFormat.PLAIN:
        return password

    hasher = _HASH_FUNCS.get(fmt)
    if not hasher:
        raise ValueError(f"Unsupported hash format: {hash_format}")

    digest = hasher(password)
    if include_plain:
        return f"{digest}:{password}" if reverse_pair else f"{password}:{digest}"
    return digest


def stream_hasher(
    stream: Iterable[str],
    hash_format: HashFormat | str = HashFormat.PLAIN,
    include_plain: bool = False,
    reverse_pair: bool = False,
) -> Iterator[str]:
    """Stream generator applying cryptographic hashing and formatting."""
    fmt = HashFormat(hash_format) if isinstance(hash_format, str) else hash_format
    if fmt == HashFormat.PLAIN:
        yield from stream
        return

    for pwd in stream:
        yield format_hash_entry(
            pwd, hash_format=fmt, include_plain=include_plain, reverse_pair=reverse_pair
        )
