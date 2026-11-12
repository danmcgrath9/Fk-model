"""The 9am list (12 Nov 2026, founder: "let's do updated scratching and pricing at 8:30am, so I am ready to bet at 9am",
after "we can get on for $1,000 - $2,000 win with all bookies"). Our live price mixed with the market now,
log p = 0.20 log(ours) + 1.00 log(1 / price now), renormalised per race (night/t_blend_bsp.py, fitted out of sample);
a runner whose price now is at least 1.05x the blend's price is on the list. Stake to win $1,000 a bookie ($2,000 at the
metro tracks), the minimum bet limit. First starters and scratched runners are never on it; blend price $1.60-$15.
    python3.13 blend_9am.py PREFIX TAG     -> data/live_bets/PREFIX-9am.csv and a table
Prices now: the meeting's -prices.txt (third field, the market when the morning's prices were pulled)."""
import csv, json, math, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(here, "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
pre, tag = sys.argv[1:3]
venue = pre[11:].replace("-", " ").title()
lim = 2000.0 if pre[11:].split("-")[0] in ("flemington", "caulfield", "moonee", "sandown") else 1000.0
now = {}
for l in open(f"{L}/{pre}-prices.txt"):
    pa = [x.strip() for x in l.split("#")[0].split(",")]
    if len(pa) >= 3 and pa[0].isdigit() and not pa[2].upper().startswith("SCR"):
        try: now[(int(pa[0]), norm(pa[1]))] = float(pa[2])
        except ValueError: pass
v6 = json.load(open(f"{L}/{pre}-{tag}-v6.json"))
fs = set()
if os.path.exists(f"{L}/{pre}-{tag}-first-starters.json"):
    x = json.load(open(f"{L}/{pre}-{tag}-first-starters.json")); fs = {norm(str(h).split("|")[-1]) for h in (x if isinstance(x, list) else x.keys())}
num = {}
if os.path.exists(f"{L}/{pre}-entry-numbers.txt"):
    for l in open(f"{L}/{pre}-entry-numbers.txt"):
        p_ = l.strip().split("|")
        if len(p_) == 5 and p_[0].isdigit(): num[(int(p_[0]), norm(p_[2]))] = p_[1]
by = {}
for r in v6: by.setdefault(int(r["race"]), []).append(r)
rows = []
for rc, rs in sorted(by.items()):
    pr = [r for r in rs if r["p"] > 0 and (rc, norm(r["horse"])) in now and now[(rc, norm(r["horse"]))] > 1]
    if len(pr) < 4: continue
    tp = sum(r["p"] for r in pr)
    w = {norm(r["horse"]): math.exp(0.20 * math.log(r["p"] / tp) + 1.00 * math.log(1 / now[(rc, norm(r["horse"]))])) for r in pr}
    sw = sum(w.values())
    for r in pr:
        k = (rc, norm(r["horse"])); pn = now[k]; bp = sw / w[k[1]]; ours = tp / r["p"]
        if k[1] in fs or not (1.6 <= bp <= 15) or pn < 1.05 * bp: continue
        stake = lim / (pn - 1)
        rows.append(dict(date=pre[:10], venue=venue, race=rc, number=num.get(k, ""), horse=r["horse"], our_price=f"{ours:.2f}",
                         blend_price=f"{bp:.2f}", price_now=f"{pn:.2f}", take_at_or_above=f"{1.05 * bp:.2f}",
                         to_win=f"{lim:.0f}", stake_a_bookie=f"{stake:.0f}"))
out = f"{L}/{pre}-9am.csv"
with open(out, "w", newline="") as fh:
    w_ = csv.DictWriter(fh, fieldnames=["date", "venue", "race", "number", "horse", "our_price", "blend_price", "price_now",
                                        "take_at_or_above", "to_win", "stake_a_bookie"]); w_.writeheader(); w_.writerows(rows)
print(f"{out}: {len(rows)} horses")
if rows:
    print("| Race | # | Horse | Ours | Blend | Now | Take at or above | Stake a bookie (to win) |\n|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| R{r['race']} | {r['number']} | {r['horse']} | ${r['our_price']} | ${r['blend_price']} | ${r['price_now']} | ${r['take_at_or_above']} | ${r['stake_a_bookie']} (${r['to_win']}) |")
