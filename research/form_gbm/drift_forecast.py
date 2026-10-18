"""Firm or drift: how far the market is expected to move a runner from the open to BSP, for staking the BetMatic orders
(18 Oct 2026, founder: "if it's certain factors that have a better ROI, why aren't we weighting those more", then
"let's do it"; tested in t_drift_gbm.py and, as the orders actually fire, in t_drift_orders.py).

The forecast y = predicted log(BSP chance / opening chance), from a LightGBM model on the dataset's form inputs (the
v9 columns), the opening chance, the field size and our price against the open (log our chance - log opening chance).
Our value bets split into thirds by y: the forecast-to-drift third, the middle and the forecast-to-firm third. The
stake multiplier is DRIFT_MULT / 1 / FIRM_MULT on those thirds (founder's choice 18 Oct: drop the drift third, x2 on
the firm third; t_drift_orders.py has both versions).

An order is built before the market exists, so the forecast is worked out at each step's own price: the opening
chance at a price t is (1/t) / the median opening book for the race's field size (from the training races).

    python3.13 drift_forecast.py train      in the live model dir: writes drift_model.txt and drift_meta.json"""
import json, os, numpy as np
DRIFT_MULT, FIRM_MULT = 0.0, 2.0
MODEL, META = "drift_model.txt", "drift_meta.json"
PARAMS = dict(objective="regression", learning_rate=0.03, num_leaves=15, min_data_in_leaf=80, feature_fraction=0.3,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, verbose=-1, seed=1)
ROUNDS = 600


def design(X, pm, price, field, book):
    """Model inputs: form columns, log opening chance, field, log our chance - log opening chance."""
    qo = (1.0 / np.asarray(price, float)) / np.asarray(book, float)
    return np.column_stack([np.asarray(X, np.float32), np.log(qo), np.asarray(field, np.float32),
                            np.log(np.asarray(pm, float)) - np.log(qo)]).astype(np.float32)


def value_rows(pm, o):
    """The bets the live orders would hold at this open (min odds rule, price band, 3x ceiling)."""
    q = 1 / np.maximum(pm, 1e-9); E = np.where(o < 4, 1.15, 1.2)
    mo = 0.95 * (E / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78)
    return (q >= 1.6) & (q <= 15) & (o >= mo) & (o < 3 * q)


def fit(X, pm, o, field, book_actual, y, rows, book_by_field):
    """Train on `rows`; thresholds are the thirds of the forecast over the value bets in `rows`, at their minimum odds."""
    import lightgbm as lgb
    r = np.where(rows)[0]
    bst = lgb.train(PARAMS, lgb.Dataset(design(X[r], pm[r], o[r], field[r], book_actual[r]), y[r]), ROUNDS)
    # thirds of what the ORDER sees: the forecast at each value bet's minimum odds (its first step), not at the open
    v = np.where(rows & value_rows(pm, o))[0]
    E = np.where(o[v] < 4, 1.15, 1.2); mo = 0.95 * (E / pm[v] ** 0.82) ** (1 / 0.78)
    fz = bst.predict(design(X[v], pm[v], mo, field[v], [book_by_field.get(int(f), np.nan) for f in field[v]]))
    t1, t2 = np.quantile(fz, [1 / 3, 2 / 3])
    return bst, float(t1), float(t2)


class Forecast:
    def __init__(self, d="."):
        import lightgbm as lgb
        self.bst = lgb.Booster(model_file=os.path.join(d, MODEL))
        m = json.load(open(os.path.join(d, META)))
        self.cols, self.t1, self.t2 = m["cols"], m["t1"], m["t2"]
        self.book = {int(k): v for k, v in m["book_by_field"].items()}

    def book_for(self, field):
        ks = sorted(self.book); return self.book[min(ks, key=lambda k: abs(k - field))]

    def y(self, xrow, pm, price, field):
        return float(self.bst.predict(design(xrow[None, :], [pm], [price], [field], [self.book_for(field)]))[0])

    def mult(self, xrow, pm, price, field, drift_mult=DRIFT_MULT, firm_mult=FIRM_MULT):
        y = self.y(xrow, pm, price, field)
        return (drift_mult if y < self.t1 else firm_mult if y >= self.t2 else 1.0), y


def load_training(ds="../model_v9/model_ds.npz", preds="blend_hold.npz", start="2026-05-06"):
    """Holdout races with every opening price and BSP; our price = stage 2 (blend_hold.npz p2, refitted before 6 May)."""
    z = np.load(ds, allow_pickle=True); ri = z["race_idx"]; nR = int(ri.max()) + 1
    p2 = np.load(preds)["p2"]; o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"].astype(float) == 1
    ok = np.isfinite(o) & (o > 1) & np.isfinite(bs) & (bs > 1)
    cnt = np.bincount(ri, minlength=nR)
    full = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (z["date"] >= start)
    hold_r = np.bincount(ri, weights=(np.isfinite(p2) & (p2 > 0)).astype(float), minlength=nR) == cnt
    m = (full & hold_r)[ri]
    def norm(v):
        s = np.bincount(ri, weights=np.where(m, v, 0), minlength=nR); return np.where(m, v / np.where(s[ri] > 0, s[ri], 1), np.nan)
    book_actual = np.bincount(ri, weights=np.where(m, 1 / np.where(ok, o, 2), 0), minlength=nR)[ri]
    qo = norm(1 / np.where(ok, o, 2)); qb = norm(1 / np.where(ok, bs, 2)); pm = norm(np.where(np.isfinite(p2), p2, 0))
    field = cnt[ri]
    bf = {}
    for f in np.unique(field[m]):
        bf[int(f)] = float(np.median(book_actual[m & (field == f)]))
    return dict(X=np.asarray(z["X"], np.float32), cols=[str(c) for c in z["cols"]], ri=ri, date=z["date"][ri], m=m,
                pm=pm, o=o, bs=bs, won=won, qo=qo, qb=qb, y=np.log(qb) - np.log(qo), field=field,
                book_actual=book_actual, book_by_field=bf)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["train"]:
        T = load_training(); m = T["m"]
        bst, t1, t2 = fit(T["X"], T["pm"], T["o"], T["field"], T["book_actual"], T["y"], m, T["book_by_field"])
        bst.save_model(MODEL)
        json.dump(dict(cols=T["cols"], t1=t1, t2=t2, book_by_field=T["book_by_field"], rows=int(m.sum()),
                       trained_on=f"holdout races from 2026-05-06 to {max(T['date'][m])}, stage-2 v6 price"), open(META, "w"), indent=1)
        print(f"{MODEL}: {m.sum()} runners; thirds of the forecast on value bets at y < {t1:.3f} (drift) and y >= {t2:.3f} (firm)")
