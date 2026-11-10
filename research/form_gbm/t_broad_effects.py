"""The few BROAD effects behind the wide search, each on a big sample (10 Nov 2026). t_wide_search.py found 54 of 720
narrow rules making money in all three periods when about 72 would by luck alone, so the narrow rules are mostly noise.
These are a handful of broad questions, written before looking, each pooled over a wide price range so the samples are
big: is the longshot bias there, do drifters lose, do firmers win, does our model's disagreement with BSP mean anything.
Actual winners against BSP-expected (A/E) with a 95% band, and profit, per period."""
import os, sys
import numpy as np
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
src = open(os.path.join(HERE, "t_wide_search.py")).read()
ns = {"__file__": os.path.join(HERE, "t_wide_search.py")}; exec(src[src.index("import collections"):src.index("# ---- the grid")], ns)
BT, LV = ns["BT"], ns["LV"]
Q = [
    ("LAY", "every runner $15-$60 (the longshot bias)", lambda D: (D["bsp"] >= 15) & (D["bsp"] < 60)),
    ("LAY", "every runner $8-$15", lambda D: (D["bsp"] >= 8) & (D["bsp"] < 15)),
    ("LAY", "drifted 1.5x from open, $8-$60", lambda D: (D["bsp"] >= 8) & (D["bsp"] < 60) & (D["bsp"] >= 1.5 * D["open"])),
    ("LAY", "firmed 1.5x from open, $8-$60", lambda D: (D["bsp"] >= 8) & (D["bsp"] < 60) & (D["bsp"] * 1.5 <= D["open"])),
    ("LAY", "model likes it (BSP >= 1.5x ours), $8-$60", lambda D: (D["bsp"] >= 8) & (D["bsp"] < 60) & (D["bsp"] >= 1.5 * D["ours"])),
    ("LAY", "model against (BSP <= ours/1.5), $8-$60", lambda D: (D["bsp"] >= 8) & (D["bsp"] < 60) & (D["bsp"] * 1.5 <= D["ours"])),
    ("BACK", "every runner $1.5-$8", lambda D: (D["bsp"] >= 1.5) & (D["bsp"] < 8)),
    ("BACK", "firmed 1.5x from open, $1.5-$8", lambda D: (D["bsp"] >= 1.5) & (D["bsp"] < 8) & (D["bsp"] * 1.5 <= D["open"])),
    ("BACK", "drifted 1.5x from open, $1.5-$8", lambda D: (D["bsp"] >= 1.5) & (D["bsp"] < 8) & (D["bsp"] >= 1.5 * D["open"])),
    ("BACK", "model likes it (BSP >= 1.3x ours), $1.5-$8", lambda D: (D["bsp"] >= 1.5) & (D["bsp"] < 8) & (D["bsp"] >= 1.3 * D["ours"])),
    ("BACK", "model against (BSP <= ours/1.3), $1.5-$8", lambda D: (D["bsp"] >= 1.5) & (D["bsp"] < 8) & (D["bsp"] * 1.3 <= D["ours"])),
    ("BACK", "our top pick, $1.5-$8", lambda D: (D["bsp"] >= 1.5) & (D["bsp"] < 8) & (D["mrank"] == 1)),
]
print("A/E = winners / BSP-expected (95% band); a lay needs A/E under about 0.92, a back over about 1.08, to beat commission")
for side, name, fn in Q:
    print(f"\n{side} {name}")
    for per, D in (("H1", BT), ("H2", BT), ("LIVE", LV)):
        sel = fn(D) & ~D["fs"] & (D["per"] == per) & np.isfinite(D["open"] if "open" in name else D["bsp"])
        b, w = D["bsp"][sel], D["won"][sel]; e = np.sum(1 / b); v = np.sum((1 / b) * (1 - 1 / b))
        ae = w.sum() / e; lo_, hi_ = (w.sum() - 1.96 * np.sqrt(v)) / e, (w.sum() + 1.96 * np.sqrt(v)) / e
        pl = (np.where(w, -(b - 1), 0.92) if side == "LAY" else np.where(w, (b - 1) * 0.92, -1.0)).sum()
        print(f"  {per:4} {len(b):5d} bets {int(w.sum()):4d} won ({e:6.1f})  A/E {ae:.2f} [{lo_:.2f}-{hi_:.2f}]  {pl:+8.1f}u ({100*pl/max(len(b),1):+.0f}%)")
