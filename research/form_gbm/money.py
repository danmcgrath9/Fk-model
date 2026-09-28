import numpy as np, bench as b, json
D = b.load(); tr, te = b.split(); ri = D["race_idx"]; pre = D["pre_jump"]
g = np.load("p_final.npy")
cfg = json.load(open("form_price.json")); Z = np.nan_to_num(np.stack([D["X"][:, D["colidx"][f]] for f in cfg["features"]], 1).astype(float))
old = b.softmax_races(Z @ b.clogit(Z, tr, D["won"], ridge=30.0))
def bets(p, races, ev_min):
    m = b.runner_mask(races) & np.isfinite(D["open"]) & (D["open"] > 1) & (1 / np.maximum(p, 1e-9) < 50)
    ev = p * D["open"] - 1
    sel = m & (ev > ev_min) & (D["open"] < 3 * (1 / np.maximum(p, 1e-9)))
    won = D["won"][sel] == 1
    op, bsp = D["open"][sel], np.where(np.isfinite(D["bsp"]), D["bsp"], D["open"])[sel]
    n = sel.sum()
    r_open = (op[won].sum() - n) / n if n else np.nan
    r_bsp = (bsp[won].sum() - n) / n if n else np.nan
    se = np.std(np.where(won, op, 0) - 1) / np.sqrt(max(n, 1))
    return n, won.sum(), r_open, se, r_bsp
for nm, p in (("old form price (deployed)", old), ("final model", g)):
    for label, rs in (("all test", te), ("live-pulled", te[pre[te]])):
        for ev in (0.1, 0.2, 0.3):
            n, w, ro, se, rb = bets(p, rs, ev)
            print(f"{nm:26s} {label:12s} value>{ev:.0%}: bets {n:5d} winners {w:4d}  at open {ro:+.1%} ±{se:.0%}  at BSP {rb:+.1%}")
    # top pick
    for label, rs in (("all test", te),):
        m = b.runner_mask(rs); best = {}
        for i in np.where(m)[0]:
            r = ri[i]
            if r not in best or p[i] > p[best[r]]: best[r] = i
        idx = np.array(list(best.values())); won = D["won"][idx] == 1
        op = D["open"][idx]; ok = np.isfinite(op)
        print(f"{nm:26s} top pick: {len(idx)} races, won {won.mean():.1%}, at open {(op[won & ok].sum() - ok.sum()) / ok.sum():+.1%}")
