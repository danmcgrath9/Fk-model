"""greyhound/sealed.py: a payload sealed to a public key comes back only with the private key; CRCs catch a bad copy."""
import json
import shutil
import subprocess

import pytest

from greyhound import sealed as S

pytestmark = pytest.mark.skipif(shutil.which("openssl") is None, reason="needs the openssl command")


def keypair(tmp_path):
    priv, pub = tmp_path / "priv.pem", tmp_path / "pub.pem"
    subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(priv)],
                   check=True, capture_output=True)
    subprocess.run(["openssl", "pkey", "-in", str(priv), "-pubout", "-out", str(pub)], check=True, capture_output=True)
    return priv, pub


def test_round_trip_and_nothing_readable_in_the_lines(tmp_path):
    priv, pub = keypair(tmp_path)
    plain = json.dumps({"dog": "KIWI EVOCA", "grv_rating": 98, "grv_price": 1.95}).encode()
    lines, sha = S.seal(plain, pub)
    text = "\n".join(lines)
    assert "KIWI" not in text and "98" not in text.split("SEALED")[0]
    assert all(ln.startswith("SEALED ") and len(ln.split()) == 4 for ln in lines) and S.check_lines(lines) == []
    assert S.unseal(list(reversed(lines)), priv) == plain and len(sha) == 64


def test_a_miscopied_line_is_named(tmp_path):
    _, pub = keypair(tmp_path)
    lines, _ = S.seal(b"x" * 500, pub)
    p = lines[1].split()
    p[3] = ("A" if p[3][0] != "A" else "B") + p[3][1:]
    lines[1] = " ".join(p)
    assert S.check_lines(lines) == [1]
