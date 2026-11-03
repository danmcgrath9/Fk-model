"""Chasing the firm after the open (3 Nov 2026, founder: "Do all the testing like that"; Ranarsson $4 open, $2.05 at
9:30am, $1.85 SP, won). Our sheet bets (every live rule, v10 holdout) joined to Form King's price path after the open
(fluc_after_open.md: 15 min, 1 h, 3 h, 6 h, 12 h after the open, 9:30am race day, 1 h before, last) for the meetings
both cover (to 13 Oct). Rule: at time T, if the price has firmed to k x the open or shorter, bet the sheet's stake AGAIN
at that price. Settled at that price less 7%. Shown beside the same horses' open bet and BSP."""
import numpy as np, csv
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
rid = z["race_id"].astype(str); hid = z["horse_id"].astype(str)
key = {(a, b): i for i, (a, b) in enumerate(zip(rid[ri], hid))}
t = open("../fluc_after_open.md").read(); rows = list(csv.DictReader(t.split("CSV-BEGIN")[1].split("CSV-END")[0].strip().splitlines()))
COLS = ["a15m", "a1h", "a3h", "a6h", "a12h", "am930", "b1h", "last"]
LBL = {"a15m": "15 min after the open", "a1h": "1 hour after", "a3h": "3 hours after", "a6h": "6 hours after", "a12h": "12 hours after", "am930": "9:30am race day", "b1h": "1 hour before", "last": "last price"}
px = {}
for r in rows:
    i = key.get((r["race_id"], r["horse_id"]))
    if i is None: continue
    px[i] = {c: (float(r[c]) if r.get(c) else None) for c in COLS}; px[i]["fopen"] = float(r["open"]) if r.get("open") else None
b = plan(pmS); idx = np.array([i for i, _ in b]); st = {i: s for i, s in b}
have = [i for i in idx if i in px and px[i]["fopen"]]
print(f"sheet bets with a price path: {len(have)} of {len(idx)} (meetings to 13 Oct)")
ours = 1 / pmS
def settle(ii, price, stake):
    return np.array([stake[i] * (price[i] - 1) * 0.93 if won[i] else -stake[i] for i in ii])
print(f"\n{'when':24s} {'rule':30s} {'n':>4s} {'won':>4s} {'ROI at that price':>17s} {'same horses at open':>19s} {'at BSP':>7s} {'kept firming to BSP':>19s}")
for c in COLS:
    for k, lab in ((0.7, "firmed to 0.7x open or shorter"), (0.85, "firmed to 0.85x or shorter"), (1.01, "all with a price (no filter)")):
        ii = [i for i in have if px[i][c] and px[i][c] <= k * px[i]["fopen"] and (k < 1 or True)]
        if k >= 1: ii = [i for i in have if px[i][c]]
        if len(ii) < 15: continue
        pT = {i: px[i][c] for i in ii}; s = {i: st[i] for i in ii}
        plT = settle(ii, pT, s); plO = settle(ii, {i: o[i] for i in ii}, s); plB = np.array([s[i] * (bs[i] - 1) * 0.92 if won[i] else -s[i] for i in ii])
        tot = sum(s.values()); kept = np.mean([bs[i] < pT[i] for i in ii])
        print(f"{LBL[c]:24s} {lab:30s} {len(ii):4d} {sum(won[i] for i in ii):4d} {100*plT.sum()/tot:+16.0f}% {100*plO.sum()/tot:+18.0f}% {100*plB.sum()/tot:+6.0f}% {100*kept:18.0f}%")
print("\nthe firmers (0.7x or shorter at 9:30am) by our price:")
ii = [i for i in have if px[i]["am930"] and px[i]["am930"] <= 0.7 * px[i]["fopen"]]
for lo, hi in ((1.6, 3), (3, 5), (5, 8), (8, 15.01)):
    jj = [i for i in ii if lo <= ours[i] < hi]
    if len(jj) < 8: print(f"  ours ${lo:g}-${hi:g}: {len(jj)} (too few)"); continue
    pT = {i: px[i]["am930"] for i in jj}; s = {i: st[i] for i in jj}; tot = sum(s.values())
    print(f"  ours ${lo:g}-${hi:g}: {len(jj)} bets, {sum(won[i] for i in jj)} won, at 9:30 price {100*settle(jj, pT, s).sum()/tot:+.0f}%, ours exp {sum(pmS[i] for i in jj):.1f}, median 9:30 price / ours {np.median([pT[i]/ours[i] for i in jj]):.2f}")
