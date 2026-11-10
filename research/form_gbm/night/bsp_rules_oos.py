"""The ten tracked Betfair SP rules on months that never chose them (night of 10 Nov 2026).
The rules came from t_both_samples.py / t_back_rules.py on 10 Nov: backtest June-July, August-8 Oct, and the live weeks.
Everything before June 2026 is untouched: Jul-Dec 2025 and Jan-May 2026, 2,900 races. Rules that only read the open
and BSP are exact there. Rules that read OUR price use the walk-forward trees for 2026 (trained before each fold) and
the cross-fitted three-model blend for 2025; both are stage 1, a little blunter than the live stage-2 price.
1u a bet at BSP, 8% commission, first starters out, races with one winner and a BSP on every runner.
    python3.13 bsp_rules_oos.py   (night folder)"""
import numpy as np
import nl
D, ri, nR, date, won, o, bs = nl.D, nl.ri, nl.nR, nl.date, nl.won, nl.o, nl.bs
P = np.where(date >= "2026-06-03", np.load("preds/base_A.npy"), np.where(date >= "2026-01-01", np.load("preds/base_B.npy"), np.load("p_oof_chal.npy"))).astype(float)
ours = 1 / np.maximum(P, 1e-9); fsr = D["X"][:, list(D["cols"]).index("firstStarter")] == 1
okb = np.isfinite(bs) & (bs > 1); rok = (np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
ok = rok[ri] & ~fsr; op = np.where(np.isfinite(o) & (o > 1), o, np.nan)
favb = np.full(nR, np.inf); np.minimum.at(favb, ri, np.where(okb, bs, np.inf)); fav = np.abs(bs - favb[ri]) < 1e-9
RULES = [("Lay $8-$12, BSP >= 1.6x ours (current)", "LAY", (bs >= 8) & (bs < 12) & (bs >= 1.6 * ours), True),
         ("Lay $15-$40, BSP >= 1.5x ours (current)", "LAY", (bs >= 15) & (bs <= 40) & (bs >= 1.5 * ours), True),
         ("Lay $25-$40, drifted 2x from open", "LAY", (bs >= 25) & (bs < 40) & (bs >= 2 * op), False),
         ("Lay $25-$40, BSP <= ours/1.6", "LAY", (bs >= 25) & (bs < 40) & (bs * 1.6 <= ours), True),
         ("Lay $8-$12, firmed 1.5x from open", "LAY", (bs >= 8) & (bs < 12) & (bs * 1.5 <= op), False),
         ("Lay $12-$15, drifted 1.25x from open", "LAY", (bs >= 12) & (bs < 15) & (bs >= 1.25 * op), False),
         ("Back $3-$5, firmed 1.5x from open", "BACK", (bs >= 3) & (bs < 5) & (bs * 1.5 <= op), False),
         ("Back $4-$7, firmed 1.5x from open", "BACK", (bs >= 4) & (bs < 7) & (bs * 1.5 <= op), False),
         ("Back BSP fav $4-$7, ours >= 1.6x BSP (current)", "BACK", fav & (bs >= 4) & (bs < 7) & (ours >= 1.6 * bs), True),
         ("Back $4-$7, ours >= 1.6x BSP (any runner)", "BACK", (bs >= 4) & (bs < 7) & (ours >= 1.6 * bs), True)]
PER = (("Jul-Sep25", "2025-07-01", "2025-10-01"), ("Oct-Dec25", "2025-10-01", "2026-01-01"), ("Jan-Mar26", "2026-01-01", "2026-04-01"), ("Apr-2Jun26", "2026-04-01", "2026-06-03"),
       ("3Jun-8Oct (chosen on)", "2026-06-03", "2026-10-09"), ("9Oct-9Nov (live)", "2026-10-09", "2027-01-01"))
print("| rule | reads our price? | " + " | ".join(p[0] for p in PER) + " | THE FOUR UNTOUCHED PERIODS | verdict |\n|" + "---|" * (len(PER) + 4))
for name, side, m, needs in RULES:
    m = np.nan_to_num(m.astype(float), nan=0) > 0; m &= ok; u = np.where(won, -(bs - 1), 0.92) if side == "LAY" else np.where(won, (bs - 1) * 0.92, -1.0)
    cells = []; pos = 0; tn = tw = 0; te = tu = 0.0
    for k, (_, lo, hi) in enumerate(PER):
        g = m & (date >= lo) & (date < hi); n, w, e, x = int(g.sum()), int(won[g].sum()), float(np.sum(1 / bs[g])), float(u[g].sum())
        cells.append(f"{n} {w} ({e:.1f}) {x:+.1f}u")
        if k < 4: pos += x > 0; tn += n; tw += w; te += e; tu += x
    v = "HOLDS (4 of 4)" if pos == 4 else "holds 3 of 4" if pos == 3 and tu > 0 else "FAILS" if tu <= 0 else "mixed"
    print(f"| {name} | {'yes' if needs else 'no'} | " + " | ".join(cells) + f" | {tn} bets, {tw} won ({te:.1f}), {tu:+.1f}u ({100*tu/max(tn,1):+.1f}% a bet) | {v} |")
print("\ncells: bets, winners (winners BSP expected), units")
