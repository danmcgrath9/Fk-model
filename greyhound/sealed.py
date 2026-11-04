"""Seal a results payload so a public Actions log can carry it unread (5 Nov 2026).

GRV's Topaz data is for personal use and must never sit anywhere public, and this repository's Actions logs and run
artifacts are public. A run that has to hand back per-runner Topaz values (tonight's card: GRV's rating, pre-race
price, tips) seals them: a fresh AES-256 key encrypts the gzip'd payload (openssl enc, CBC, PBKDF2) and the key is
encrypted to `greyhound/keys/card_pub.pem` (RSA-OAEP-SHA256). The private key never enters the repository. The log
gets base64 lines, each with a CRC32 so a copied line can be checked one at a time, and the SHA-256 of the plaintext.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import os
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

PUBKEY = Path(__file__).resolve().parent / "keys" / "card_pub.pem"
WIDTH = 76


def _run(args, data: bytes | None = None) -> bytes:
    return subprocess.run(args, input=data, capture_output=True, check=True).stdout


def seal(plain: bytes, pubkey: Path = PUBKEY) -> tuple[list[str], str]:
    """(log lines, sha256 hex of the plaintext). Each line: 'SEALED nnn crc32hex base64chunk'."""
    with tempfile.TemporaryDirectory() as td:
        kf = Path(td) / "k"
        kf.write_text(os.urandom(32).hex())
        body = _run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "100000", "-salt", "-pass", f"file:{kf}"],
                    gzip.compress(plain, 9))
        kenc = _run(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(pubkey), "-pkeyopt",
                     "rsa_padding_mode:oaep", "-pkeyopt", "rsa_oaep_md:sha256", "-in", str(kf)])
    blob = base64.b64encode(struct.pack(">H", len(kenc)) + kenc + body).decode()
    chunks = [blob[i:i + WIDTH] for i in range(0, len(blob), WIDTH)]
    lines = [f"SEALED {i:03d} {zlib.crc32(c.encode()) & 0xffffffff:08x} {c}" for i, c in enumerate(chunks)]
    return lines, hashlib.sha256(plain).hexdigest()


def check_lines(lines: list[str]) -> list[int]:
    """Indexes of lines whose chunk does not match its CRC (a copying error), in order."""
    bad = []
    for ln in lines:
        _, idx, crc, chunk = ln.split()
        if f"{zlib.crc32(chunk.encode()) & 0xffffffff:08x}" != crc:
            bad.append(int(idx))
    return bad


def unseal(lines: list[str], privkey: Path) -> bytes:
    rows = sorted((ln.split() for ln in lines if ln.startswith("SEALED ")), key=lambda p: int(p[1]))
    blob = base64.b64decode("".join(p[3] for p in rows))
    n = struct.unpack(">H", blob[:2])[0]
    kenc, body = blob[2:2 + n], blob[2 + n:]
    with tempfile.TemporaryDirectory() as td:
        kf, bf = Path(td) / "kenc", Path(td) / "body"
        kf.write_bytes(kenc)
        bf.write_bytes(body)
        key = _run(["openssl", "pkeyutl", "-decrypt", "-inkey", str(privkey), "-pkeyopt", "rsa_padding_mode:oaep",
                    "-pkeyopt", "rsa_oaep_md:sha256", "-in", str(kf)])
        pf = Path(td) / "pass"
        pf.write_bytes(key)
        gz = _run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "100000", "-pass", f"file:{pf}", "-in", str(bf)])
    return gzip.decompress(gz)
