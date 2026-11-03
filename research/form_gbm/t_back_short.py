"""The other way (3 Nov 2026, founder: "if it's such bad ROI, surely the other way is a bet"): BACK at BSP the horses the
market has shorter than we do, by BSP band and by how much shorter, favourites and all runners, both halves. Flat 1u,
8% commission on winnings."""
import numpy as np
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1; rdate = z["date"].astype(str); date = rdate[ri]
p10 = np.load("v10_profit_preds.npz")["p10"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1
okr = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan); ours = 1 / pm
minb = np.full(nR, np.inf)
for i in np.where(m)[0]: minb[ri[i]] = min(minb[ri[i]], bs[i])
fav = m & (bs <= minb[ri] + 1e-9)
cut = sorted(set(rdate[race_ok]))[len(set(rdate[race_ok])) // 2]; early = date < cut
print("| back 1u at BSP | half | bets | won | BSP expected | A/E | ROI |\n|---|---|---|---|---|---|---|")
def row(name, g):
    for h, hm in (("early", early), ("late", ~early)):
        gg = g & hm; n = gg.sum()
        if n == 0: continue
        exp = (1 / bs[gg]).sum(); w = won[gg].sum(); pl = np.where(won[gg], (bs[gg] - 1) * 0.92, -1.0).sum()
        print(f"| {name} | {h} | {n} | {w} | {exp:.1f} | {w/exp:.2f} | {100*pl/n:+.0f}% |")
for b0, b1 in ((1.5, 2.5), (2.5, 4), (4, 7), (7, 12)):
    for k in (1.3, 1.6, 2.0):
        row(f"favourite BSP ${b0}-${b1}, ours >= {k}x", fav & (bs >= b0) & (bs < b1) & (ours >= k * bs))
for b0, b1 in ((2.5, 4), (4, 7), (7, 12), (12, 20)):
    for k in (1.3, 1.6):
        row(f"any runner BSP ${b0}-${b1}, ours >= {k}x", m & (bs >= b0) & (bs < b1) & (ours >= k * bs))
row("ALL favourites", fav); row("ALL runners the market has shorter than us (ours > BSP)", m & (ours > bs))
