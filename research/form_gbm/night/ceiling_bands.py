"""The ceiling, band by band (11 Nov 2026, founder: "show me the stats on the price increase").
Walk-forward three-model blend (queue 3), 1 Jan - 9 Nov 2026, plain live rules at Form King's open with NO ceiling
(edge 1.2, $1.60-$15, three steps, Kelly stake capped at 10u, flat 16c deduction, first starters in), then every bet
sorted by how far the open was above our price.
    python3.13 ceiling_bands.py   (night folder)"""
import numpy as np
import nl
src = open("seed_stability.py").read(); exec(src.split("def line(")[0].split("import nl, stake_rule")[1].replace("hm = {", "import stake_rule\nhm = {"))
P = {f: np.load(f"preds/m_live_blend_{f}.npy").astype(float) for f in "AB"}
B = {}
for f in "AB": B.update(bets(P[f], hm[f], ceil=1e9))
idx = np.array(sorted(B)); st = np.array([B[i][0] for i in idx]); pl = np.array([B[i][1] for i in idx])
pm = np.where(nl.date[idx] >= "2026-06-03", P["A"][idx], P["B"][idx]); ratio = nl.o[idx] * pm; qb = nl.q[idx]
print("| open / our price | bets | a month | won | BSP expected | median open | median BSP | staked | profit | on stakes | periods in profit |\n|---|---|---|---|---|---|---|---|---|---|---|")
PER = [(lo, hi) for f in "BA" for _, lo, hi in nl.PERIODS[f][:2]]
for lo, hi in ((1.0, 1.4), (1.4, 1.7), (1.7, 2.2), (2.2, 3.0), (3.0, 4.0), (4.0, 6.0), (6.0, 99), (3.0, 6.0), (1.0, 3.0)):
    m = (ratio >= lo) & (ratio < hi); n = int(m.sum())
    if not n: continue
    pos = sum(pl[m & (nl.date[idx] >= a) & (nl.date[idx] < b_)].sum() > 0 for a, b_ in PER)
    lab = f"{lo:g}x-{hi:g}x" if hi < 99 else f"{lo:g}x+"
    print(f"| {lab} | {n} | {n/10.3:.0f} | {int(nl.won[idx][m].sum())} | {qb[m].sum():.1f} | ${np.median(nl.o[idx][m]):.1f} | ${np.nanmedian(nl.bs[idx][m]):.1f} | {st[m].sum():.0f}u | {pl[m].sum():+.0f}u | {100*pl[m].sum()/st[m].sum():+.0f}% | {pos} of 4 |")
m = (ratio >= 3) & (ratio < 6); w = nl.won[idx][m]
print(f"\nthe 3x-6x bets: average stake {st[m].mean():.2f}u (all bets {st.mean():.2f}u); winners' opens: " + ", ".join(f"${x:.0f}" for x in sorted(nl.o[idx][m][w])))
print(f"biggest single winner {pl[m].max():+.0f}u; profit without the three biggest winners {pl[m].sum() - np.sort(pl[m])[-3:].sum():+.0f}u; longest losing run {max(len(s) for s in ''.join('L' if x < 0 else 'W' for x in pl[m][np.argsort(nl.date[idx][m], kind='stable')]).split('W'))} bets")
print(f"beat BSP (open above BSP): {100*np.mean(nl.o[idx][m] > nl.bs[idx][m]):.0f}% of them; median BSP / open {np.nanmedian(nl.bs[idx][m] / nl.o[idx][m]):.2f}")
