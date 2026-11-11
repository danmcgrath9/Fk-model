"""Settle a meeting's lay book at Betfair SP. python settle_lays.py LAYS.csv RESULTS.txt [--unit 200]

LAYS.csv is lay_sheet.py's output (race, horse, ours, lay_if_bsp_at_least, lay_if_bsp_at_most, price_now, note);
RESULTS.txt is scripts/meeting_results.py's output ("R3 Horse Name   finish 1  SP 7.0  BSP 7.82"). The rule as
written in TIPPING_RULES.md: lay 1u (the backer's stake) at BSP when BSP sits inside the runner's band; a loser
returns +0.92u (8% commission), a winner costs BSP - 1. A runner with no result or no BSP is void and named, a
runner the sheet excluded (first starter, international) never lays. Prints one line per lay and the totals.
"""
import argparse, csv, re, sys
COMM = 0.08
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
ap = argparse.ArgumentParser(); ap.add_argument("lays"); ap.add_argument("results"); ap.add_argument("--unit", type=float, default=200.0)   # a lay is $200 (founder, 3 Nov 2026: "lays at $200 and backs at $100")
a = ap.parse_args()
res = {}
for line in open(a.results):
    m = re.match(r"R(\d+)\s+(.+?)\s+finish\s+(\S+)\s+SP\s+(\S+)\s+BSP\s+(\S+)", line.strip())
    if not m: continue
    rn, name, fin, sp, bsp = m.groups()
    def num(x):
        try: return float(x)
        except ValueError: return None
    b = num(bsp)
    b = b if b is not None and b > 1 else None   # Form King writes a missing Betfair SP as 0.0 (Ballarat R6-R8, 11 Nov 2026): void, not "outside the band"
    res[(int(rn), norm(name))] = (fin if fin != "None" else None, num(sp), b)
lays, void, skipped = [], [], 0
for r in csv.DictReader(open(a.lays)):
    rn = int(r["race"]); note = (r.get("note") or "").strip()
    if "excluded" in note: skipped += 1; continue
    lo, hi = float(r["lay_if_bsp_at_least"]), float(r["lay_if_bsp_at_most"])
    fin, sp, bsp = res.get((rn, norm(r["horse"])), (None, None, None))
    if fin is None or bsp is None:
        v_ = f"R{rn} {r['horse']}" + ("" if (rn, norm(r["horse"])) in res else " (not in results)")
        if v_ not in void: void.append(v_)
        continue
    if not (lo <= bsp <= hi): continue
    won = fin in ("1", "1.0")
    pl = -(bsp - 1) if won else 1 - COMM
    lays.append((rn, r["horse"], lo, bsp, fin, pl, (r.get("band") or "15-40").strip()))
for rn, h, lo, bsp, fin, pl, band in lays:
    print(f"R{rn} {h:<22} lay at ${lo:.2f}+  BSP ${bsp:.2f}  finish {fin:>3}  {pl:+.2f}u  (${band})")
for b in sorted({x[6] for x in lays}, key=lambda b: float(b.split("-")[0])):   # each band on its own line (the $8-$12 band from 8 Nov 2026)
    g = [x for x in lays if x[6] == b]
    print(f"  band ${b}: {len(g)} lays, {sum(1 for x in g if x[5] < 0)} winners, {sum(x[5] for x in g):+.2f}u")
n, w, tot = len(lays), sum(1 for x in lays if x[5] < 0), sum(x[5] for x in lays)
print(f"{n} lays, {w} winners, {tot:+.2f}u (${tot*a.unit:+,.0f} at ${a.unit:g}); excluded by the sheet {skipped}; void {len(void)}: {', '.join(void) or 'none'}")
