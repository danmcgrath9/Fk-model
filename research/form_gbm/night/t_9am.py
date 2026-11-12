"""Any bets that win at 9am or at BSP? (12 Nov 2026, founder: "Are there any type of bets that we win 9am or bsp?")
The 10 Nov challenger's out-of-fold three-model blend on every race with timed flucs (fluc_minutes.py: Jul-Oct 2025,
Sep-Nov 2026), first starters out. 1u flat. 9am = the last fluc at or before 9:00am Melbourne on race day, no deduction;
BSP with 8% commission on a winner. Each line is shown for the two blocks separately: a type only counts if it pays in
both. Types: the open book's own bets (value at the open) by how the price moved to 9am, by our price, by edge at 9am;
and value judged AT 9am (the 9am price at least k x our price), by our price.
    python3.13 t_9am.py FLUC_MINUTES.md   (night folder)"""
import csv, io, sys
import numpy as np

z = np.load("ds/model_ds.npz", allow_pickle=True); P = np.load("p_oof_chal.npy").astype(float)
ri = z["race_idx"]; nR = len(z["race_id"]); date = z["date"].astype(str)[ri]; rid = z["race_id"].astype(str)[ri]
hid = z["horse_id"].astype(str); won = np.asarray(z["finish"], float) == 1
o = np.asarray(z["open"], float); bs = np.asarray(z["bsp"], float); fsr = z["X"][:, list(z["cols"]).index("firstStarter")] == 1
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
s = open(sys.argv[1]).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
key = {(r["race_id"], r["horse_id"]): r for r in csv.DictReader(io.StringIO(s[a:b].strip()))}
g = lambda c: np.array([float(key[(rid[i], hid[i])][c]) if (rid[i], hid[i]) in key and key[(rid[i], hid[i])][c] else np.nan for i in range(len(ri))])
p9 = g("c0900")
ours = 1 / np.maximum(P, 1e-9); mo = 0.95 * (1.2 / np.maximum(P, 1e-9) ** 0.82) ** (1 / 0.78)
base = np.isfinite(p9) & race_ok[ri] & ~fsr & (P > 0) & (ours >= 1.6) & (ours <= 15) & np.isfinite(bs) & (bs > 1)
B1 = date < "2026-01-01"; B2 = ~B1
r9 = np.where(won, p9 - 1, -1.0); rb = np.where(won, (bs - 1) * 0.92, -1.0)


def row(lab, m):
    m = m & base; out = [lab, str(int(m.sum()))]
    for r_ in (r9, rb):
        for blk in (np.ones_like(m), B1, B2):
            mm = m & blk; out.append(f"{100 * r_[mm].mean():+.0f}%" if mm.sum() >= 20 else "-")
    print("| " + " | ".join(out) + " |")


print(f"{int(base.sum())} runners priced in timed races\n")
print("| type | bets | 9am ROI | 9am Jul-Oct 25 | 9am Sep-Nov 26 | BSP ROI | BSP Jul-Oct 25 | BSP Sep-Nov 26 |\n|---|---|---|---|---|---|---|---|")
book = (o >= mo) & (o < 6 * ours)
row("THE OPEN BOOK (value at the open), all", book)
mv = p9 / o
for lab, m in (("  firmed 1.5x+ open to 9am", mv <= 1 / 1.5), ("  firmed 1.2-1.5x", (mv > 1 / 1.5) & (mv <= 1 / 1.2)),
               ("  steady", (mv > 1 / 1.2) & (mv < 1.2)), ("  drifted 1.2x+", mv >= 1.2)):
    row(lab, book & m)
for lo, hi in ((1.6, 3), (3, 5), (5, 8), (8, 15.01)):
    row(f"  ours ${lo:g}-${hi:g}", book & (ours >= lo) & (ours < hi))
e9 = p9 / ours
for lo, hi in ((0, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, 1.5), (1.5, 99)):
    row(f"  9am price {lo:g}-{hi:g}x ours", book & (e9 >= lo) & (e9 < hi))
print("| VALUE AT 9AM (any runner) | | | | | | | |")
for k in (1.2, 1.5, 2.0):
    row(f"  9am price >= {k:g}x ours", e9 >= k)
    for lo, hi in ((1.6, 4), (4, 8), (8, 15.01)):
        row(f"    and ours ${lo:g}-${hi:g}", (e9 >= k) & (ours >= lo) & (ours < hi))
print("| VALUE AT BSP (any runner) | | | | | | | |")
eb = bs / ours
for k in (1.2, 1.5, 2.0):
    row(f"  BSP >= {k:g}x ours", eb >= k)
