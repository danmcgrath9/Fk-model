"""Settle a day's harness paper picks (19 Nov 2026): every runner's result and TAB first/last price for the day, sealed.

    python research/harness/bw_settle.py --day YYYY-MM-DD --pub PUBKEY_B64

Fetches the day's Australian harness races from Betwatch (BETWATCH_API_KEY) and seals, per runner: track, race,
number, horse, finishing position (None when Betwatch has no result yet), scratched, TAB's first price and TAB's last
price before the start. The picks themselves are matched where the private key is (the picks were sealed the same
way), so the public log carries counts only.
"""
import argparse, base64, json, math, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bw_data import runner_rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--day", required=True); ap.add_argument("--pub", required=True)
    a = ap.parse_args()
    from greyhound import betwatch as B, sealed
    races = B.fetch_day(B._session(), a.day, ("Harness",), B.AU_STATES)
    rows = []
    for r in races:
        for x in runner_rows(B.compact(r)):
            val = lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else v
            rows.append({"track": x["bw_track"], "race": x["race_number"], "no": x["number"], "horse": x["horse_name"],
                         "pos": None if val(x["bw_pos"]) is None else int(x["bw_pos"]), "scratched": x["scratched"],
                         "tab_first": val(x["tab_open"]), "tab_last": val(x["tab_last"])})
    done = len({(r["track"], r["race"]) for r in rows if r["pos"] is not None})
    print(f"{a.day}: {len(races)} races, {len(rows)} runners; races with a result {done}")
    with tempfile.NamedTemporaryFile("wb", suffix=".pem", delete=False) as fh:
        fh.write(base64.b64decode(a.pub)); pk = fh.name
    lines, sha = sealed.seal(json.dumps({"day": a.day, "runners": rows}).encode(), Path(pk))
    print(f"sha256 {sha}"); print("\n".join(lines))


if __name__ == "__main__":
    main()
