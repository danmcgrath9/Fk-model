"""The open book's own bets struck at BSP instead (11 Nov 2026): if TAB will not take the stake, is BSP a home for them?
Walk-forward three-model blend, 1 Jan - 9 Nov 2026, live rules with no ceiling; every bet settled 1u flat at the open
(16c deduction) and at BSP (8% commission), by open / our price.
    python3.13 open_bets_at_bsp.py   (night folder)"""
import numpy as np
import nl
src = open("seed_stability.py").read(); exec(src.split("def line(")[0].split("import nl, stake_rule")[1].replace("hm = {", "import stake_rule\nhm = {"))
P = {f: np.load(f"preds/m_live_blend_{f}.npy").astype(float) for f in "AB"}; B = {}
for f in "AB": B.update(bets(P[f], hm[f], ceil=1e9))
idx = np.array(sorted(B)); w = nl.won[idx]; o_ = nl.o[idx]; b_ = nl.bs[idx]; q_ = nl.q[idx]
pm = np.where(nl.date[idx] >= "2026-06-03", P["A"][idx], P["B"][idx]); ratio = o_ * pm
at_open = np.where(w, (o_ - 1) * 0.84, -1.0); at_bsp = np.where(w, (b_ - 1) * 0.92, -1.0)
PER = [(lo, hi) for f in "BA" for _, lo, hi in nl.PERIODS[f][:2]]
print("| open / our price | bets | won | BSP expected | flat at the open | flat at BSP | periods BSP pays |\n|---|---|---|---|---|---|---|")
for lo, hi in ((1.0, 1.4), (1.4, 1.7), (1.7, 2.2), (2.2, 3.0), (3.0, 6.0), (1.0, 6.0)):
    m = (ratio >= lo) & (ratio < hi) & np.isfinite(b_); pos = sum(at_bsp[m & (nl.date[idx] >= a) & (nl.date[idx] < z)].sum() > 0 for a, z in PER)
    print(f"| {lo:g}x-{hi:g}x | {int(m.sum())} | {int(w[m].sum())} | {q_[m].sum():.1f} | {100*at_open[m].mean():+.0f}% | {100*at_bsp[m].mean():+.1f}% | {pos} of 4 |")
