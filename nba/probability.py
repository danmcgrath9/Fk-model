"""Step 2: turn a projection into P(over) and P(under) for a line, then weigh it against the market.

Part A, the model on its own. Each stat is a count, so the outcome is a negative
binomial with mean = projection and a variance curve V(mu) = c0 + c1 mu + c2 mu^2 fitted
per stat to the model's OUT-OF-SAMPLE misses in 2023/24 (trained 2020-2022). The textbook
form (V = mu + alpha mu^2) was tried first and is wrong for points: their spread grows
roughly in a straight line with the projection (sd 4.7 at 6 points, 8.8 at 30), so it was
too narrow for bench players and too wide for stars. Checked on 2024/25 against synthetic
half-point lines next to every projection.

Part B, against the bookie. The first line test showed the model alone is overconfident
when it disagrees with the line (it said 73%, the bet won 55%): the line knows things the
model does not. So the probability we bet on is a blend,
    logit p = a + b * logit p_model + c * logit p_market,
with p_market the line's no-vig probability. a, b, c are fitted on 2024/25 lines ONLY and
scored on 2025/26 lines, which they never saw. If c dwarfs b the model adds little.

    python nba/probability.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, stats

import project as pr
from features import DATA

STATS = pr.TARGETS


def nb_params(mu: np.ndarray, var_coef) -> tuple[np.ndarray, np.ndarray]:
    """scipy's nbinom(n, p) with mean mu and variance V(mu); V is kept above mu (the
    smallest a count can spread), which the four stats never get near in practice."""
    mu = np.maximum(np.asarray(mu, float), 0.05)
    c = np.asarray(var_coef, float)
    if c.ndim == 1:
        c = np.broadcast_to(c, (len(mu), 3))
    v = np.maximum(c[:, 0] + c[:, 1] * mu + c[:, 2] * mu ** 2, mu * 1.05)
    return mu ** 2 / (v - mu), mu / v


def fit_variance(mu: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Least squares of squared miss on (1, mu, mu^2): the variance curve."""
    X = np.column_stack([np.ones_like(mu), mu, mu ** 2])
    coef, *_ = np.linalg.lstsq(X, (y - mu) ** 2, rcond=None)
    return coef


def p_over_under(mu, line, var_coef):
    """P(stat > line), P(stat < line). Whole-number lines can push."""
    n, p = nb_params(mu, var_coef)
    line = np.asarray(line, float)
    over = stats.nbinom.sf(np.floor(line), n, p)          # > line
    under = stats.nbinom.cdf(np.ceil(line) - 1, n, p)     # < line
    return over, under


def oos_2023() -> pd.DataFrame:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok]
    train = df[df.season.isin([2020, 2021, 2022]) & df.min_ewm5.notna()]
    val = df[df.season == 2023]
    p = pr.fit_predict(train, val).merge(val[["gameId", "personId", "min_ewm5", "gp_season"]],
                                          on=["gameId", "personId"])
    return p[pr.propable(p)]


def fit_alphas() -> dict[str, np.ndarray]:
    """Variance curve per stat (name kept from the first, one-number version)."""
    p = oos_2023()
    return {st: fit_variance(np.maximum(p[f"{st}_proj"].to_numpy(), 0.05), p[st].to_numpy())
            for st in STATS}


def calibration_table(pred: np.ndarray, hit: np.ndarray, bins=(0, .2, .3, .4, .5, .6, .7, .8, 1)):
    t = pd.DataFrame({"pred": pred, "hit": hit})
    t["bin"] = pd.cut(t.pred, bins)
    return t.groupby("bin", observed=True).agg(n=("hit", "size"), predicted=("pred", "mean"),
                                               actual=("hit", "mean"))


def model_check(alphas) -> None:
    """Part A: on all prop-able players in 2024/25, with a half-point line just under or
    over each projection, does a 60% say come in 60% of the time?"""
    proj = pd.read_parquet(DATA / "projections.parquet")
    f = pd.read_parquet(DATA / "features.parquet")[["gameId", "personId", "min_ewm5", "gp_season"]]
    proj = proj.merge(f, on=["gameId", "personId"])
    proj = proj[pr.propable(proj) & (proj.season == 2024)]
    rng = np.random.default_rng(0)
    print("A. The model alone, 2024/25, synthetic half-point lines around each projection")
    for st in STATS:
        mu = np.maximum(proj[f"{st}_proj"].to_numpy(), 0.05)
        line = np.floor(mu + rng.uniform(-3, 3, len(mu)) * (1 if st == "pts" else 0.5)) + 0.5
        line = np.maximum(line, 0.5)
        over, _ = p_over_under(mu, line, alphas[st])
        hit = (proj[st].to_numpy() > line).astype(float)
        t = calibration_table(over, hit)
        t = t[t.n >= 100]                       # a bin of 10 games is noise
        worst = (t.predicted - t.actual).abs().max()
        c = alphas[st]
        print(f"   {st:<5} V = {c[0]:.2f} + {c[1]:.2f} mu + {c[2]:.3f} mu^2   worst bin off by {worst:.1%}")
        print("     " + "  ".join(f"{r.predicted:.0%}->{r.actual:.0%}" for r in t.itertuples()))
    print()


def logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def fit_blend(d: pd.DataFrame) -> np.ndarray:
    """Logistic regression of 'went over' on logit p_model and logit p_market (pushes out)."""
    X = np.column_stack([np.ones(len(d)), logit(d.p_model.to_numpy()), logit(d.p_mkt.to_numpy())])
    y = d.went_over.to_numpy()

    def nll(w):
        z = X @ w
        return np.sum(np.logaddexp(0, z) - y * z)
    return optimize.minimize(nll, np.array([0, 0.5, 0.5]), method="BFGS").x


def blend(d: pd.DataFrame, w: np.ndarray) -> np.ndarray:
    z = w[0] + w[1] * logit(d.p_model.to_numpy()) + w[2] * logit(d.p_mkt.to_numpy())
    return 1 / (1 + np.exp(-z))


def log_loss(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def flat_bets(d: pd.DataFrame, p_over: np.ndarray, edges=(0.0, 0.02, 0.04, 0.06)) -> None:
    """Bet the side whose EV at the recorded price clears the edge. Pushes refund."""
    rng = np.random.default_rng(0)
    ev_o = p_over * d.dec_over - 1
    ev_u = (1 - p_over) * d.dec_under - 1
    side = np.where(ev_o >= ev_u, "over", "under")
    ev = np.maximum(ev_o, ev_u)
    dec = np.where(side == "over", d.dec_over, d.dec_under)
    pnl = np.where(d.result == "push", 0.0, np.where(d.result == side, dec - 1, -1.0))
    t = pd.DataFrame({"date": d.date, "pnl": pnl, "ev": ev, "st": d.st})
    print(f"     {'edge':>5} {'bets':>5} {'ROI':>7}   95% bootstrap (by game date)")
    for e in edges:
        b = t[t.ev >= e]
        if len(b) < 30:
            print(f"     {e:>5.0%} {len(b):>5}  too few bets to say anything")
            continue
        g = b.groupby("date").pnl.agg(["sum", "size"])
        s, c = g["sum"].to_numpy(), g["size"].to_numpy()
        idx = rng.integers(0, len(g), (2000, len(g)))
        boot = s[idx].sum(1) / c[idx].sum(1)
        print(f"     {e:>5.0%} {len(b):>5} {b.pnl.mean():>+7.1%}   "
              f"{np.percentile(boot, 2.5):+.1%} to {np.percentile(boot, 97.5):+.1%}")


def market_check(alphas) -> None:
    j = pd.read_parquet(DATA / "line_test.parquet")
    j = j[j.over_odds.notna() & j.under_odds.notna()].copy()
    # P(over | no push), to sit on the same footing as the no-vig market price
    o, u = p_over_under(np.maximum(j.proj.to_numpy(), 0.05), j.line.to_numpy(),
                        np.stack([alphas[s] for s in j.st]))
    j["p_model"] = o / (o + u)
    io, iu = 1 / j.dec_over, 1 / j.dec_under
    j["p_mkt"] = io / (io + iu)
    j = j[j.result != "push"].copy()
    j["went_over"] = (j.result == "over").astype(float)
    j["season"] = np.where(j.date < "2025-07-01", "2024/25", "2025/26")
    tr, te = j[j.season == "2024/25"], j[j.season == "2025/26"]
    w = fit_blend(tr)
    print(f"B. Against the bookie. Blend fitted on {len(tr):,} lines from 2024/25:")
    print(f"   logit p = {w[0]:+.3f} + {w[1]:.3f} x model + {w[2]:.3f} x market")
    print(f"   Scored on {len(te):,} lines from 2025/26 it never saw. Log loss, lower is better:")
    y = te.went_over.to_numpy()
    for name, p in [("market alone", te.p_mkt), ("model alone", te.p_model),
                    ("blend", blend(te, w)), ("coin flip", np.full(len(te), 0.5))]:
        print(f"     {name:<13} {log_loss(np.asarray(p), y):.4f}")
    print("\n   Calibration on 2025/26 (said -> happened):")
    for name, p in [("market alone", te.p_mkt.to_numpy()), ("model alone", te.p_model.to_numpy()),
                    ("blend", blend(te, w))]:
        t = calibration_table(p, y, bins=(0, .4, .45, .5, .55, .6, 1))
        print(f"     {name:<12} " + "  ".join(f"{r.predicted:.0%}->{r.actual:.0%} ({r.n})"
                                              for r in t.itertuples()))
    print("\n   Flat 1-unit bets on 2025/26 at the recorded prices, using the blend:")
    flat_bets(te.reset_index(drop=True), blend(te, w))
    print("\n   Same, using the model alone (the first test's approach, now calibrated):")
    flat_bets(te.reset_index(drop=True), te.p_model.to_numpy())


def main() -> None:
    alphas = fit_alphas()
    model_check(alphas)
    market_check(alphas)


if __name__ == "__main__":
    main()
