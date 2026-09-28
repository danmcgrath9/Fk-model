"""Local test bench for the Form King-only price. Same scoring as fk.backtest.score."""
import numpy as np

D = None


def load(path="ds/model_ds.npz"):
    global D
    z = np.load(path, allow_pickle=False)
    D = {k: z[k] for k in z.files}
    ri = D["race_idx"]
    n_r = int(ri.max()) + 1
    starts = np.searchsorted(ri, np.arange(n_r))
    ends = np.append(starts[1:], len(ri))
    D["starts"], D["ends"], D["n_races"] = starts, ends, n_r
    D["q"] = norm_inv(D["bsp"])
    D["mkt"] = norm_inv(D["open"])
    D["won"] = (D["finish"] == 1).astype(float)
    D["colidx"] = {c: i for i, c in enumerate(D["cols"])}
    return D


def race_fill(v, fill_mean=True):
    """per race: NaN -> race mean (or 0 when the race has none)."""
    out = v.astype(float).copy()
    ri = D["race_idx"]
    ok = ~np.isnan(out)
    s = np.bincount(ri, weights=np.where(ok, out, 0.0), minlength=D["n_races"])
    c = np.bincount(ri, weights=ok.astype(float), minlength=D["n_races"])
    m = np.where(c > 0, s / np.maximum(c, 1), 0.0)
    out[~ok] = m[ri[~ok]]
    return out


def norm_inv(price):
    inv = np.where((price > 1) & np.isfinite(price), 1.0 / np.where(price > 1, price, 2.0), np.nan)
    inv = race_fill(inv)
    inv = np.nan_to_num(inv, nan=0.0)
    tot = np.bincount(D["race_idx"], weights=inv, minlength=D["n_races"])
    n = np.bincount(D["race_idx"], minlength=D["n_races"])
    ri = D["race_idx"]
    return np.where(tot[ri] > 0, inv / np.where(tot[ri] > 0, tot[ri], 1), 1.0 / n[ri])


def softmax_races(s):
    ri = D["race_idx"]
    mx = np.full(D["n_races"], -np.inf)
    np.maximum.at(mx, ri, s)
    e = np.exp(s - mx[ri])
    return e / np.bincount(ri, weights=e, minlength=D["n_races"])[ri]


def split(share=0.7, races=None):
    """(older, newer) race masks by date, as fit_form_only.split_by_date."""
    races = np.arange(D["n_races"]) if races is None else races
    dates = D["date"][races]
    order = np.argsort(dates, kind="stable")
    cut = min(int(len(races) * share), len(races) - 1)
    day = dates[order[cut]]
    return races[dates < day], races[dates >= day]


def runner_mask(races):
    m = np.zeros(len(D["race_idx"]), bool)
    m[np.isin(D["race_idx"], races)] = True
    return m


def score(p, races):
    m = runner_mask(races)
    q, w, ri = D["q"][m], D["won"][m], D["race_idx"][m]
    pp = np.maximum(p[m], 1e-12)
    kl = np.where(q > 0, q * np.log(np.maximum(q, 1e-300) / pp), 0.0).sum() / len(races)
    ll = -np.log(pp[w == 1]).sum() / len(races)
    # top pick won
    best = {}
    for r, v, isw in zip(ri, pp, w):
        if r not in best or v > best[r][0]:
            best[r] = (v, isw)
    top = np.mean([b[1] for b in best.values()])
    return kl, ll, top


def fmt(name, sc):
    return f"{name:44s} KL {sc[0]:.4f}  LL {sc[1]:.4f}  top {sc[2]:.1%}"


def clogit(Z, races, target, ridge=10.0, iters=40):
    """Conditional logit by Newton with ridge. Z: runners x k (no NaN)."""
    m = runner_mask(races)
    Zm, ri = Z[m], D["race_idx"][m]
    t = target[m]
    # renumber races
    _, rr = np.unique(ri, return_inverse=True)
    nR = rr.max() + 1
    k = Z.shape[1]
    b = np.zeros(k)
    for _ in range(iters):
        s = Zm @ b
        mx = np.full(nR, -np.inf); np.maximum.at(mx, rr, s)
        e = np.exp(s - mx[rr]); p = e / np.bincount(rr, weights=e, minlength=nR)[rr]
        tr = np.bincount(rr, weights=t, minlength=nR)[rr]
        g = Zm.T @ (t - p * tr) - ridge * b
        zbar = np.stack([np.bincount(rr, weights=p * Zm[:, j], minlength=nR) for j in range(k)], 1)
        W = Zm * np.sqrt(p * tr)[:, None]
        H = W.T @ W - (zbar * np.sqrt(np.bincount(rr, weights=t, minlength=nR))[:, None]).T @ (zbar * np.sqrt(np.bincount(rr, weights=t, minlength=nR))[:, None])
        H += ridge * np.eye(k)
        step = np.linalg.solve(H, g)
        b += step
        if np.abs(step).max() < 1e-7:
            break
    return b
