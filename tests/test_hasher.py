"""
Unit tests for hasher.py (MD5, SHA1, SHA256, NTLM hashing).
"""

from wordlist_gen.hasher import (
    HashFormat,
    _pure_python_md4,
    format_hash_entry,
    md5_hash,
    ntlm_hash,
    sha1_hash,
    sha256_hash,
    stream_hasher,
)


def test_md5_hash():
    assert md5_hash("admin") == "21232f297a57a5a743894a0e4a801fc3"


def test_sha1_hash():
    assert sha1_hash("admin") == "d033e22ae348aeb5660fc2140aec35850c4da997"


def test_sha256_hash():
    assert (
        sha256_hash("admin")
        == "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
    )


def test_ntlm_hash_test_vectors():
    # Specification Test 2: NTLM Hash Correctness
    # "admin" -> ntlm: 209c6174da490caeb422f3fa5a7ae634
    assert ntlm_hash("admin") == "209c6174da490caeb422f3fa5a7ae634"

    # Known NTLM vector for "password": 8846f7eaee8fb117ad06bdd830b7586c
    assert ntlm_hash("password") == "8846f7eaee8fb117ad06bdd830b7586c"

    # "Password" (titlecase)
    assert ntlm_hash("Password") == "a4f49c406510bdcab6824ee7c30fd852"


def test_pure_python_md4_fallback():
    # RFC 1320 test suite vectors
    assert _pure_python_md4(b"").hex() == "31d6cfe0d16ae931b73c59d7e0c089c0"
    assert _pure_python_md4(b"a").hex() == "bde52cb31de33e46245e05fbdbd6fb24"
    assert _pure_python_md4(b"abc").hex() == "a448017aaf21d8525fc10ae87aa6729d"
    assert (
        _pure_python_md4(b"message digest").hex()
        == "d9130a8164549fe818874806e1c7014b"
    )


def test_format_hash_entry():
    pwd = "secret"
    # Plain
    assert format_hash_entry(pwd, HashFormat.PLAIN) == "secret"

    # Hash only
    md5_val = md5_hash(pwd)
    assert format_hash_entry(pwd, HashFormat.MD5) == md5_val

    # Include plain: <plain>:<hash>
    assert format_hash_entry(pwd, HashFormat.MD5, include_plain=True) == f"{pwd}:{md5_val}"

    # Reverse pair: <hash>:<plain>
    assert (
        format_hash_entry(pwd, HashFormat.MD5, include_plain=True, reverse_pair=True)
        == f"{md5_val}:{pwd}"
    )


def test_stream_hasher():
    words = ["admin", "root"]
    hashed = list(stream_hasher(words, HashFormat.MD5, include_plain=False))
    assert hashed == [md5_hash("admin"), md5_hash("root")]

    plain_stream = list(stream_hasher(words, HashFormat.PLAIN))
    assert plain_stream == words
