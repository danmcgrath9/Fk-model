"""Follow-up to bsp_scan.py: the two current lay rules and the three survivors on the live-style price, period by period.
    python3.13 bsp_scan2.py   (night folder)"""
import numpy as np
src = open("bsp_scan.py").read().split('print("1. WHEN WE DISAGREE')[0]; exec(src)
mv = op / bs; r = bs / ours
RULES = [("CURRENT lay $8-$12, BSP >= 1.6x ours", "LAY", (bs >= 8) & (bs < 12) & (r >= 1.6)),
         ("CURRENT lay $15-$40, BSP >= 1.5x ours", "LAY", (bs >= 15) & (bs <= 40) & (r >= 1.5)),
         ("back $3-$5, firmed 1.5x+ from the open", "BACK", (bs >= 3) & (bs < 5) & (mv >= 1.5)),
         ("lay $20-$40, BSP 0.6x ours or less", "LAY", (bs >= 20) & (bs < 40) & (r < 0.6)),
         ("back $8-$40, firmed 1.25x+ and we rate it 10%+ shorter than BSP", "BACK", (bs >= 8) & (bs <= 40) & (mv >= 1.25) & (r >= 1.1)),
         ("back $8-$20, same", "BACK", (bs >= 8) & (bs < 20) & (mv >= 1.25) & (r >= 1.1)),
         ("back $20-$40, same", "BACK", (bs >= 20) & (bs <= 40) & (mv >= 1.25) & (r >= 1.1)),
         ("back $8-$40, firmed 1.5x+ and we rate it 10%+ shorter", "BACK", (bs >= 8) & (bs <= 40) & (mv >= 1.5) & (r >= 1.1)),
         ("back $8-$40, firmed 1.25x+ and we rate it 25%+ shorter", "BACK", (bs >= 8) & (bs <= 40) & (mv >= 1.25) & (r >= 1.25)),
         ("back $8-$40, firmed 1.25x+ (no model)", "BACK", (bs >= 8) & (bs <= 40) & (mv >= 1.25))]
months = 16.3
for name, side, m in RULES:
    m = np.nan_to_num(m.astype(float), nan=0) > 0; m &= ok; u = ul if side == "LAY" else ub
    n, w, e = int(m.sum()), int(won[m].sum()), float(qb[m].sum()); z = (w - e) / np.sqrt(float(np.sum(qb[m] * (1 - qb[m]))))
    per = [f"{int((m & p).sum())}: {int(won[m & p].sum())} v {qb[m & p].sum():.1f}, {u[m & p].sum():+.0f}u" for p in pm]
    liab = float(np.sum((bs[m] - 1))) if side == "LAY" else n
    print(f"{name}\n   {n} bets ({n/months:.0f} a month), {w} won v {e:.1f} by BSP (z {z:+.1f}), {u[m].sum():+.1f}u at 1u ({100*u[m].sum()/n:+.1f}% a bet; {u[m].sum()/months:+.1f}u a month)"
          + (f", {100*u[m].sum()/liab:+.2f}% of the liability" if side == "LAY" else "") + f", median BSP ${np.median(bs[m]):.1f}\n   by period: " + " | ".join(per))
