"""Anything else we can win at Betfair SP? A full sweep (11 Nov 2026, founder: "Anything else we can win at bsp").
The price: for 2026 the LIVE-STYLE price, stage 2 trained inside each fold (s2_check.py) and blended with the open
(0.82 / 0.22) as live does; for Jul-Dec 2025 the cross-fitted three-model blend with the same open blend (no walk-forward
stage 2 exists that far back). Six periods; 1u a bet at BSP, 8% commission on a win, first starters out, races with one
winner and a BSP on every runner. A cell counts only if it pays in at least five of the six periods.
    python3.13 bsp_scan.py   (night folder, after s2_check.py)"""
import numpy as np
import nl
D, ri, nR, date, won, o, bs = nl.D, nl.ri, nl.nR, nl.date, nl.won, nl.o, nl.bs
sm_ = nl.b.softmax_races; ld = lambda f: np.load(f).astype(float)
P0 = np.where(date >= "2026-06-03", ld("preds/s2_base_A.npy"), np.where(date >= "2026-01-01", ld("preds/s2_base_B.npy"), ld("p_oof_chal.npy")))
op = np.where(np.isfinite(o) & (o > 1), o, np.nan)
raw = np.where(np.isfinite(op), np.exp(0.82 * np.log(np.maximum(P0, 1e-9)) + 0.22 * np.log(1 / np.where(np.isfinite(op), op, 1.0))), P0)
P = raw / np.bincount(ri, weights=raw, minlength=nR)[ri]; ours = 1 / np.maximum(P, 1e-9)
fsr = D["X"][:, list(D["cols"]).index("firstStarter")] == 1
okb = np.isfinite(bs) & (bs > 1); rok = (np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
ok = rok[ri] & ~fsr; qb = 1 / np.where(okb, bs, 1e9)
PER = (("Jul-Sep25", "2025-07-01", "2025-10-01"), ("Oct-Dec25", "2025-10-01", "2026-01-01"), ("Jan-Mar26", "2026-01-01", "2026-04-01"), ("Apr-2Jun26", "2026-04-01", "2026-06-03"),
       ("3Jun-8Oct26", "2026-06-03", "2026-10-09"), ("9Oct-9Nov26", "2026-10-09", "2027-01-01"))
pm = [(date >= lo) & (date < hi) for _, lo, hi in PER]
ub = np.where(won, (bs - 1) * 0.92, -1.0); ul = np.where(won, -(bs - 1), 0.92)


def stat(m, side=None):
    m = m & ok; n, w, e = int(m.sum()), int(won[m].sum()), float(qb[m].sum()); b, l = float(ub[m].sum()), float(ul[m].sum())
    bp = [float(ub[m & p].sum()) for p in pm]; lp = [float(ul[m & p].sum()) for p in pm]
    return dict(n=n, w=w, e=e, ae=w / max(e, 1e-9), b=b, l=l, bpos=sum(x > 0 for x in bp), lpos=sum(x > 0 for x in lp), bp=bp, lp=lp,
                z=(w - e) / max(np.sqrt(float(np.sum(qb[m] * (1 - qb[m])))), 1e-9))


print("1. WHEN WE DISAGREE WITH BSP, WHO IS RIGHT? every runner $1.50-$40 at BSP, by BSP / our price (over 1 = we rate it shorter than the market does)")
print("| BSP / ours | runners | won | BSP expected | we expected | A/E v BSP | back at BSP | lay at BSP | periods back pays | periods lay pays |\n|---|---|---|---|---|---|---|---|---|---|")
RB = ((0, 0.5, "under 0.5 (market has it half our price)"), (0.5, 0.67, "0.5-0.67"), (0.67, 0.8, "0.67-0.8"), (0.8, 0.95, "0.8-0.95"), (0.95, 1.05, "agree"), (1.05, 1.25, "1.05-1.25"),
      (1.25, 1.5, "1.25-1.5"), (1.5, 2.0, "1.5-2"), (2.0, 99, "2+ (we have it half the market's price)"))
r = bs / ours; band = (bs >= 1.5) & (bs <= 40)
for lo, hi, lab in RB:
    m = band & (r >= lo) & (r < hi); s = stat(m); eo = float(P[m & ok].sum())
    print(f"| {lab} | {s['n']} | {s['w']} | {s['e']:.0f} | {eo:.0f} | {s['ae']:.2f} | {100*s['b']/max(s['n'],1):+.1f}% | {100*s['l']/max(s['n'],1):+.1f}% a lay | {s['bpos']} of 6 | {s['lpos']} of 6 |")

print("\n2. THE GRID: BSP band x BSP / ours. Each cell: bets, A/E v BSP, back % a bet (periods it pays) / lay % a lay (periods it pays)")
PB = ((1.5, 3), (3, 5), (5, 8), (8, 12), (12, 20), (20, 40)); RG = ((0, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, 1.25), (1.25, 1.6), (1.6, 99))
print("| BSP | " + " | ".join(f"BSP/ours {a:g}-{b_:g}" if b_ < 99 else f"BSP/ours {a:g}+" for a, b_ in RG) + " |\n|---|" + "---|" * len(RG))
flags = []
for lo, hi in PB:
    cells = []
    for a, b_ in RG:
        m = (bs >= lo) & (bs < hi) & (r >= a) & (r < b_); s = stat(m)
        cells.append(f"{s['n']}, {s['ae']:.2f}, back {100*s['b']/max(s['n'],1):+.0f}% ({s['bpos']}) / lay {100*s['l']/max(s['n'],1):+.0f}% ({s['lpos']})")
        for side, tot, pos, per in (("BACK", s["b"], s["bpos"], s["bp"]), ("LAY", s["l"], s["lpos"], s["lp"])):
            if s["n"] >= 150 and pos >= 5 and tot > 0: flags.append((side, f"${lo:g}-${hi:g}", f"{a:g}-{b_:g}" if b_ < 99 else f"{a:g}+", s, tot, per))
    print(f"| ${lo:g}-${hi:g} | " + " | ".join(cells) + " |")
print(f"\ncells that pay in 5+ of 6 periods on 150+ bets (72 tried; about {72 * (7 / 64) * 0.5:.0f} expected by luck if every bet were fair before commission, fewer after it):")
for side, pb, rb, s, tot, per in flags:
    print(f"  {side} {pb}, BSP/ours {rb}: {s['n']} bets, {s['w']} won ({s['e']:.1f} expected, z {s['z']:+.1f}), {tot:+.1f}u ({100*tot/s['n']:+.1f}% a bet), by period " + ", ".join(f"{x:+.0f}" for x in per))

print("\n3. NO MODEL AT ALL: every runner by BSP band (is there a favourite or longshot lean at BSP?)")
print("| BSP | runners | won | expected | A/E | back at BSP | periods back pays | lay | periods lay pays |\n|---|---|---|---|---|---|---|---|---|")
for lo, hi in ((1, 2), (2, 3), (3, 5), (5, 8), (8, 12), (12, 20), (20, 40), (40, 100), (100, 1001)):
    s = stat((bs >= lo) & (bs < hi))
    print(f"| ${lo}-${hi} | {s['n']} | {s['w']} | {s['e']:.0f} | {s['ae']:.2f} | {100*s['b']/max(s['n'],1):+.1f}% | {s['bpos']} of 6 | {100*s['l']/max(s['n'],1):+.1f}% | {s['lpos']} of 6 |")

print("\n4. OUR TOP PICK and the favourite")
rank_ours = np.zeros(len(ri)); order = np.lexsort((-P, ri)); first = np.searchsorted(ri[order], np.arange(nR)); rank_ours[order] = np.arange(len(ri)) - first[ri[order]] + 1
favb = np.full(nR, np.inf); np.minimum.at(favb, ri, np.where(okb, bs, np.inf)); fav = np.abs(bs - favb[ri]) < 1e-9
for lab, m in (("our top pick, any price", rank_ours == 1), ("our top pick and the BSP favourite", (rank_ours == 1) & fav), ("our top pick, NOT the BSP favourite", (rank_ours == 1) & ~fav),
               ("the BSP favourite, not our top pick", fav & (rank_ours != 1)), ("our top pick at BSP $3-$8", (rank_ours == 1) & (bs >= 3) & (bs < 8)),
               ("our top pick, we have it 1.25x+ shorter than BSP", (rank_ours == 1) & (r >= 1.25)), ("our top pick, BSP shorter than ours", (rank_ours == 1) & (r < 1.0))):
    s = stat(m); print(f"  {lab}: {s['n']} bets, {s['w']} won ({s['e']:.1f} expected, A/E {s['ae']:.2f}), back {s['b']:+.1f}u ({100*s['b']/max(s['n'],1):+.1f}%, pays in {s['bpos']} of 6), lay {100*s['l']/max(s['n'],1):+.1f}% ({s['lpos']} of 6)")

print("\n5. THE MOVE AND OUR PRICE TOGETHER (open / BSP over 1 = firmed)")
mv = op / bs
for lab, m in (("firmed 1.25x+ AND we rate it shorter than BSP", (mv >= 1.25) & (r >= 1.1)), ("firmed 1.25x+ AND we rate it longer than BSP", (mv >= 1.25) & (r < 0.9)),
               ("drifted 1.25x+ AND we rate it shorter than BSP", (mv <= 0.8) & (r >= 1.1)), ("drifted 1.25x+ AND we rate it longer than BSP", (mv <= 0.8) & (r < 0.9)),
               ("firmed 1.5x+ at BSP $3-$5 (the tracked island)", (mv >= 1.5) & (bs >= 3) & (bs < 5)), ("firmed 1.5x+ at BSP $3-$5 AND we rate it $6 or shorter", (mv >= 1.5) & (bs >= 3) & (bs < 5) & (ours <= 6)),
               ("firmed 1.5x+ at BSP $3-$5 AND we rate it over $6", (mv >= 1.5) & (bs >= 3) & (bs < 5) & (ours > 6))):
    for pb_lab, pbm in (("$1.50-$8", (bs >= 1.5) & (bs < 8)), ("$8-$40", (bs >= 8) & (bs <= 40))) if "island" not in lab and "$3-$5" not in lab else (("", np.ones(len(bs), bool)),):
        s = stat(m & pbm); print(f"  {lab} {pb_lab}: {s['n']} bets, {s['w']} won ({s['e']:.1f}, A/E {s['ae']:.2f}), back {100*s['b']/max(s['n'],1):+.1f}% ({s['bpos']} of 6), lay {100*s['l']/max(s['n'],1):+.1f}% ({s['lpos']} of 6)")
