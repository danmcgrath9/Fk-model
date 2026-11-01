"""Binary inputs (flags) the band audit skipped: winners v expected with the flag off and on, both date halves."""
import numpy as np
exec(open("t_input_calib.py").read().split("out = []")[0])
print(f"{'flag':42s} {'off: won/exp':>14s} {'on: won/exp':>13s} {'on, 1st half':>13s} {'on, 2nd half':>13s}")
rows = []
for j, c in enumerate(cols):
    v = X[:, j]; f = m & np.isfinite(v); u = np.unique(v[f])
    if len(u) != 2 or f.sum() < 2000: continue
    on = f & (v == u[1]); off = f & (v == u[0])
    def r(g): e = pm[g].sum(); return (won[g].sum() / e if e >= 25 else np.nan, e)
    a, b, b1, b2 = r(off), r(on), r(on & h1), r(on & ~h1)
    if np.isfinite(b[0]): rows.append((abs(b[0] - 1), c, a, b, b1, b2))
for _, c, a, b, b1, b2 in sorted(rows, reverse=True)[:20]:
    print(f"{c:42s} {a[0]:7.2f} ({a[1]:5.0f}) {b[0]:6.2f} ({b[1]:5.0f}) {b1[0] if np.isfinite(b1[0]) else float('nan'):6.2f} ({b1[1]:4.0f}) {b2[0] if np.isfinite(b2[0]) else float('nan'):6.2f} ({b2[1]:4.0f})")
