"""Every nominated horse's recent runs with Form King's rating for each, from the horse
form stored in fk.horses (Get Horse Form, as fetched by price_nominations --refresh).
Read-only, no Form King calls.

    python scripts/nomination_form.py --file data/nominations/X.txt [--runs 6]

Rating is Form King's rating at the weights carried (atWeights), else its WFA rating.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import load_settings  # noqa: E402
from fk import fields as F  # noqa: E402
from fk.db import Db  # noqa: E402
from price_nominations import key  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--runs", type=int, default=6)
    a = ap.parse_args()
    names = [ln.strip() for ln in Path(a.file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    db = Db(load_settings().database_url)
    rows = db.conn.execute(
        """select distinct on (k) k, name, raw from (
             select regexp_replace(regexp_replace(lower(name), '\\(.*?\\)', '', 'g'), '[^a-z0-9]', '', 'g') k, name, raw,
                    profile_fetched_at from fk.horses where raw ? 'pastEvents') h
           where k = any(%s) order by k, profile_fetched_at desc nulls last""", (sorted({key(n) for n in names}),)).fetchall()
    held = {k: raw for k, _, raw in rows}
    out = []
    for n in names:
        raw = held.get(key(n))
        runs = []
        if raw:
            for p in sorted(F.horse_form_past_events(raw), key=lambda p: F.past_event_date(p) or "", reverse=True):
                if p.get("spell") or p.get("scratched") or not F.past_event_date(p):
                    continue
                r, m = F.run_ratings(p), F.run_market(p)
                runs.append({"date": r["date"], "track": r.get("track"), "dist": r.get("distance"), "going": m.get("going"),
                             "fin": r.get("finish"), "of": r.get("runners"), "margin": m.get("margin"), "sp": m.get("sp"),
                             "rating": r.get("atWeights") or r.get("wfaRat") or r.get("wfa"), "wfa": r.get("wfaRat") or r.get("wfa"),
                             "trial": r.get("trial")})
                if len(runs) >= a.runs:
                    break
        out.append({"horse": n, "held": bool(raw), "runs": runs})
        print(f"\n{n}" + ("" if raw else ": no Form King form held"))
        for x in runs:
            print(f"  {x['date']} {x['track'] or '?':16} {x['dist'] or '?'}m {'TRIAL ' if x['trial'] else ''}{x['fin']}/{x['of']} "
                  f"{x['margin']}L ${x['sp']}  rating {x['rating']}  wfa {x['wfa']}")
    print("\nJSON " + json.dumps(out, default=str))


if __name__ == "__main__":
    main()
