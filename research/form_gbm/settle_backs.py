"""Settle a meeting's paper back book (3 Nov 2026). python settle_backs.py BACKS.csv RESULTS.txt [--unit 100]
BACKS.csv is lay_sheet.py's DAYPREFIX-GTAG-backs.csv (race, horse, ours, back_if_favourite_bsp_at_least/at_most, price_now);
RESULTS.txt is scripts/meeting_results.py's output. The rule: back 1u at Betfair SP the horse that is the BSP FAVOURITE
of its race when its BSP is $4 to its at_most price (our price / 1.6, capped at $7); 8% commission on a winner."""
import argparse, csv, re
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower()); COMM = 0.08
ap = argparse.ArgumentParser(); ap.add_argument("backs"); ap.add_argument("results"); ap.add_argument("--unit", type=float, default=100.0)
a = ap.parse_args()
res, favbsp = {}, {}
for line in open(a.results):
    m = re.match(r"R(\d+)\s+(.+?)\s+finish\s+(\S+)\s+SP\s+(\S+)\s+BSP\s+(\S+)", line.strip())
    if not m: continue
    rn, name, fin, _, bsp = m.groups()
    try: bsp = float(bsp)
    except ValueError: continue
    res[(int(rn), norm(name))] = (fin if fin != "None" else None, bsp)
    if fin is not None and fin != "None": favbsp[int(rn)] = min(favbsp.get(int(rn), 1e9), bsp)
bets = []
for r in csv.DictReader(open(a.backs)):
    rn = int(r["race"]); k = (rn, norm(r["horse"]))
    if k not in res or res[k][0] is None: continue
    fin, bsp = res[k]
    if abs(bsp - favbsp.get(rn, -1)) > 1e-9: continue          # not the favourite at the jump
    lo, hi = float(r["back_if_favourite_bsp_at_least"]), float(r["back_if_favourite_bsp_at_most"])
    if not (lo <= bsp <= hi): continue
    pl = (bsp - 1) * (1 - COMM) if fin == "1" else -1.0
    bets.append((rn, r["horse"], float(r["ours"]), hi, bsp, fin, pl))
for rn, h, o, hi, bsp, fin, pl in bets:
    print(f"R{rn} {h:<22} ours ${o:5.2f}  back if fav $4 to ${hi:.2f}  BSP ${bsp:.2f}  finish {fin:>3}  {pl:+.2f}u")
n = len(bets); w = sum(1 for b in bets if b[6] > 0); tot = sum(b[6] for b in bets)
print(f"{n} backs, {w} winners, {tot:+.2f}u (${tot*a.unit:+,.0f} at ${a.unit:g} a unit)")
