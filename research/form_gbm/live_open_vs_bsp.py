"""Every live meeting since we started: the open book at the price we take (Form King's open) and the same bets at
Betfair SP (12 Nov 2026, founder: "what are the returns of the Victorian model at price we take and then BSP ...
literally since we have been live - like the last 5 weeks").

The sheet of record is each meeting's -betmatic-preopen.csv. An order fills when the open is inside its band
(min_odds <= open <= max_odds, BetMatic's rule, as betmatic_html.py settles it), its units add up per horse, and the
bet is settled at the open with no deduction (founder, 1 Nov: deductions scrapped) and again at BSP with 8% commission
on a winner. A bet whose horse has no BSP is left out of BOTH columns, so the two are on the same bets. Picnic and
other paper-only meetings are listed separately.
    python3.13 live_open_vs_bsp.py"""
import collections, csv, glob, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import track_rules as T

L = T.L; nm = T.nm; COMM = 0.08
res = T.results()


def res_for(pre):
    day = pre[:10].replace("-", ""); slug = pre[11:]
    for k in (f"{slug}-{day}",):
        if k in res: return res[k]
    for k, v in res.items():
        if k.endswith(day) and k.startswith(slug): return v
    return None


rows, missing = [], []
for f in sorted(glob.glob(f"{L}/2026-*-betmatic-preopen.csv")):
    pre = os.path.basename(f)[:-len("-betmatic-preopen.csv")]
    if "-test" in pre or pre[:10] >= "2026-11-12": continue
    r = res_for(pre)
    if not r:
        missing.append(pre); continue
    op = T.opens(pre)
    hd = open(f"{L}/{pre}-prices.txt").readline() if os.path.exists(f"{L}/{pre}-prices.txt") else ""
    paper = "PAPER" in hd.upper() or "picnic" in hd.lower() or "balnarring" in pre
    by = collections.OrderedDict()
    for o in csv.DictReader(open(f)):
        k = (int(o["race"]), nm(o["horse"])); o_ = op.get(k)
        if o_ is None or o_ < float(o["min_odds"]) or (o.get("max_odds") and o_ > float(o["max_odds"])): continue
        b = by.setdefault(k, dict(horse=o["horse"], race=int(o["race"]), stake=0.0, open=o_))
        b["stake"] += float(o["stake_units"])
    for k, b in by.items():
        fin, bsp = r.get(k, (None, None))
        if fin is None and bsp is None: continue        # no result for the horse (scratched late, or not in the file)
        won = fin == "1"
        rows.append(dict(pre=pre, day=pre[:10], paper=paper, won=won, stake=b["stake"], open=b["open"], bsp=bsp,
                         pl_open=b["stake"] * (b["open"] - 1) if won else -b["stake"],
                         pl_bsp=(b["stake"] * (bsp - 1) * (1 - COMM) if won else -b["stake"]) if bsp and bsp > 1 else None,
                         horse=b["horse"], race=b["race"]))

import datetime as dt
def week(d):
    x = dt.date.fromisoformat(d); m = x - dt.timedelta(days=x.weekday()); return f"{m:%d %b}"

def table(rs, title):
    print(f"\n## {title}\n")
    print("| period | meetings | bets | won | staked | at the open | ROI | same bets at BSP | ROI | bets with no BSP |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    groups = collections.OrderedDict()
    for x in sorted(rs, key=lambda x: x["day"]): groups.setdefault("week of " + week(x["day"]), []).append(x)
    groups["ALL"] = rs
    for g, xs in groups.items():
        b = [x for x in xs if x["pl_bsp"] is not None]; nb = len(xs) - len(b)
        st = sum(x["stake"] for x in b); po = sum(x["pl_open"] for x in b); pb = sum(x["pl_bsp"] for x in b)
        print(f"| {g} | {len({x['pre'] for x in xs})} | {len(b)} | {sum(x['won'] for x in b)} | {st:.1f}u | {po:+.1f}u | "
              f"{po / max(st, 1e-9):+.0%} | {pb:+.1f}u | {pb / max(st, 1e-9):+.0%} | {nb} |")

live = [x for x in rows if not x["paper"]]; pap = [x for x in rows if x["paper"]]
table(live, "The open book, every live meeting (1u = $50)")
if pap: table(pap, "Paper-only meetings (picnic / no holdout), not in the table above")
b = [x for x in live if x["pl_bsp"] is not None]
beat = sum(1 for x in b if x["open"] > x["bsp"])
print(f"\nThe open beat BSP on {beat} of {len(b)} bets ({beat / max(len(b), 1):.0%}); median open/BSP "
      f"{sorted(x['open'] / x['bsp'] for x in b)[len(b) // 2]:.2f}.")
print(f"First meeting {min(x['day'] for x in rows)}, last {max(x['day'] for x in rows)}.")
if missing: print(f"No results file for: {', '.join(missing)}")
