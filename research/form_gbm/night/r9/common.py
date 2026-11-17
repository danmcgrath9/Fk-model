"""r9/common.py: shared loader for the 18 Nov research. Run scripts from the night folder with r9 on the path."""
import pickle, re, os
import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
MAJORS = ("tab", "sportsbet", "ladbrokes", "neds", "pointsbet", "unibet", "betr")
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True)
C = pickle.load(open(os.path.join(HERE, "r9.pkl"), "rb"))
G = C["ghosts"]                                              # (race index, name, parsed row): in the 9am market, did not run
n0 = len(z["race_idx"]); ng = len(G); n = n0 + ng
ri = np.concatenate([z["race_idx"], np.array([g[0] for g in G], int)]); nR = len(z["race_id"]); rid = z["race_id"].astype(str)
date = z["date"].astype(str)[ri]; track = z["track"].astype(str)[ri]
name = np.concatenate([z["name"].astype(str), np.array([g[1] for g in G])])
rno = np.array([int(r.rsplit("_", 1)[1]) for r in rid])[ri]
ghost = np.arange(n) >= n0
fin = np.concatenate([np.asarray(z["finish"], float), np.zeros(ng)])
ran = fin > 0                                                # ghosts and the dataset's own non-runners (finish 0) did not run
won = fin == 1; bs = np.concatenate([np.asarray(z["bsp"], float), np.full(ng, np.nan)])
cols = list(z["cols"]); fs = np.concatenate([z["X"][:, cols.index("firstStarter")] == 1, np.zeros(ng, bool)])
METRO = ("flemington", "caulfield", "moonee valley", "the valley", "sandown")
metro = np.array([any(t.lower().startswith(m) for m in METRO) for t in track])
lim = np.where(metro, 2000.0, 1000.0)
month = np.array([d[:7] for d in date])
ROWS = list(C["rows"]) + [g[2] for g in G]
tab = [r["tab"] if r else None for r in ROWS]; maj = [r["maj"] if r else None for r in ROWS]; best = [r["best"] if r else None for r in ROWS]
bk9 = [r["bk9"] if r else None for r in ROWS]; nine = np.array([r["nine"] if r else np.nan for r in ROWS])


def price_at(path, t):
    """Last price at or before time t (minutes relative to the jump); nan if none yet."""
    if path is None: return np.nan
    k = np.searchsorted(path[0], t, side="right") - 1
    return path[1][k] if k >= 0 else np.nan


def col9(bookie):
    return np.array([(d or {}).get(bookie, np.nan) for d in bk9], float)


B7 = np.column_stack([col9(k) for k in MAJORS])                     # the seven majors at 9am
T9 = B7[:, 0]
with np.errstate(all="ignore"):
    MED7 = np.nanmedian(B7, 1)
# Our chance for a ghost: the model never priced it in the final field, so it takes its 9am market share and the
# runners that ran keep their relative chances in what is left. DED = the non-runners' market share of the race at
# 9am: the deduction off a winner's winnings (TAB's scale is close to the scratched horse's share of the book).
_m = np.where(np.isfinite(MED7), MED7, T9); _inv = np.where(np.isfinite(_m) & (_m > 1), 1 / np.where(_m > 1, _m, 2), 0.0)
_tot = np.bincount(ri, weights=_inv, minlength=nR)
share = _inv / np.maximum(_tot[ri], 1e-12)
Q = np.bincount(ri, weights=np.where(ghost, share, 0.0), minlength=nR)
P0 = np.concatenate([np.load("p_oof_chal.npy").astype(float), np.zeros(ng)])
P = np.where(ghost, share, P0 * (1 - Q[ri]))
DED = np.minimum(np.bincount(ri, weights=np.where(~ran, share, 0.0), minlength=nR), 0.9)[ri]
has_ghost = (np.bincount(ri, weights=~ran, minlength=nR) > 0)[ri]


def softmax_by_race(s, ok):
    """p within each race over the runners in ok; 0 elsewhere."""
    s = np.where(ok, s, -np.inf)
    mx = np.full(nR, -np.inf); np.maximum.at(mx, ri, s)
    e = np.where(ok, np.exp(s - mx[ri]), 0.0)
    tot = np.bincount(ri, weights=e, minlength=nR)
    return np.where(ok, e / np.maximum(tot[ri], 1e-300), 0.0)


def race_ok(ok, need=4):
    """Runners in ok (ghosts included: they were in the 9am market) whose race has at least `need` of them and one winner."""
    cnt = np.bincount(ri, weights=ok, minlength=nR); w = np.bincount(ri, weights=ok & won, minlength=nR)
    miss = np.bincount(ri, weights=ran & ~ok, minlength=nR)      # a runner that ran with no 9am price: the race's book is incomplete
    return ok & (cnt[ri] >= need) & (w[ri] == 1) & (miss[ri] == 0)


def fit_cl(X, ok, l2=0.0):
    """Conditional logit: maximise the winner's log chance over races, runners in ok. X (n, k). Returns beta."""
    Xo = np.where(ok[:, None], X, 0.0); nr = len(np.unique(ri[ok]))

    def f(b):
        p = softmax_by_race(Xo @ b, ok)
        ll = np.log(np.maximum(p[ok & won], 1e-300)).sum()
        g = (Xo[ok & won].sum(0) - (p[:, None] * Xo).sum(0))
        return -(ll / nr) + l2 * (b ** 2).sum(), -(g / nr) + 2 * l2 * b
    r = minimize(f, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B")
    return r.x


def logloss(p, ok):
    m = ok & won
    return -np.log(np.maximum(p[m], 1e-300)).mean()


PERIODS = (("2025-07-01", "2025-11-01", "Jul-Oct 2025"), ("2025-11-01", "2026-03-01", "Nov 2025-Feb 2026"),
           ("2026-03-01", "2026-07-01", "Mar-Jun 2026"), ("2026-07-01", "2026-09-01", "Jul-Aug 2026"),
           ("2026-09-01", "2026-12-01", "Sep-Nov 2026"))


def bets(fair, elig, prices, thr=1.05, lo=1.6, hi=15.0, ded=True):
    """Stake to win the limit with each bookie whose price is at least thr x fair. prices (n, k). -> hit, stake, pl"""
    e = elig & ran & ~fs & np.isfinite(fair) & (fair >= lo) & (fair <= hi)        # a non-runner's bet is refunded: no bet
    hit = e[:, None] & np.isfinite(prices) & (prices >= thr * fair[:, None]) & (prices > 1)
    st = np.where(hit, lim[:, None] / np.maximum(prices - 1, 1e-9), 0.0)
    pl = np.where(hit, np.where(won[:, None], (lim * (1 - (DED if ded else 0)))[:, None], -st), 0.0)
    return hit, st, pl


def money_row(label, hit, st, pl, m):
    h = hit & m[:, None]; s, p = st[m].sum(), pl[m].sum()
    mos = sorted(set(month[h.any(1)]))
    pos = sum(pl[(month == mo) & m].sum() > 0 for mo in mos)
    return (f"| {label} | {int(h.any(1).sum())} | {int(h.sum())} | {int((h.any(1) & won).sum())} | ${s:,.0f} | ${p:+,.0f} | "
            f"{(p / s if s else 0):+.1%} | {pos} of {len(mos)} |")
MONEY_HEAD = "| | runners | bookie bets | winners | staked | profit | ROI | months up |\n|---|---|---|---|---|---|---|---|"
