"""Night lab (10-11 Nov 2026, founder: "Do every check of our model ANYTHING you can think of, research to get our model
closer to bsp and any betting strategies. You have all night").

One harness for every retrain experiment, so they are all judged the same way:
  * the live stage-1 softmax trees (lab.train, 4000 rounds, feature_fraction 0.2, extra_trees, the blanked copy), 3 seeds;
  * TWO walk-forward folds, so a change has to hold on two separate sets of unseen races:
      fold A  trained on races before 3 Jun 2026, scored 3 Jun - 9 Nov 2026 (the usual holdout: 30+ earlier tests used it)
      fold B  trained on races before 1 Jan 2026, scored 1 Jan - 2 Jun 2026 (never used as a test set before tonight)
  * KL to BSP and winner log loss are the measures; profit at the open under the live rules is shown but is far noisier;
  * every arm is paired with the base arm on the same seeds, and the base arm is run on three seed sets for the noise floor.
Results go to results.jsonl (one line per arm x fold), predictions to preds/.
Run from the night work folder (research/form_gbm scripts, ds/model_ds.npz = the datasets branch file, F9n.npy)."""
import collections, json, os, sys, time
import numpy as np, lightgbm as lgb
import lab, bench as b, gbm, stake_rule

D = lab.D; ri = lab.ri0; nR = D["n_races"]
F = np.load("F9n.npy"); NM = open("F9n_names.txt").read().split("\n")
rdate = D["date"].astype(str); date = rdate[ri]; q = D["q"]
won = np.asarray(D["finish"], float) == 1
o = np.asarray(D["open"], float); bs = np.asarray(D["bsp"], float)
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
field = np.bincount(ri, minlength=nR)[ri]
meet = np.char.add(D["track"][ri].astype(str), np.char.add("|", date)); jk = D["jockey"].astype(str)
_cnt = collections.Counter(zip(meet, jk)); only = np.array([_cnt[(m, x)] == 1 for m, x in zip(meet, jk)])
FOLDS = {"A": ("2026-06-03", "2026-06-03", "2027-01-01"), "B": ("2026-01-01", "2026-01-01", "2026-06-03")}
PERIODS = {"A": (("A1 3Jun-8Oct", "2026-06-03", "2026-10-09"), ("A2 9Oct-9Nov", "2026-10-09", "2027-01-01"), ("A all", "2026-06-03", "2027-01-01")),
           "B": (("B1 1Jan-17Mar", "2026-01-01", "2026-03-18"), ("B2 18Mar-2Jun", "2026-03-18", "2026-06-03"), ("B all", "2026-01-01", "2026-06-03"))}
DED, TIERS = 0.16, (1.0, 1.25, 1.5)
_orig_aug = lab.augmented


def train(FF, names, train_races, target, params=None, seed=0, rounds=4000, aug=True, aug_share=0.8, weight=None):
    """lab.train with a blanked-copy share and optional per-runner weights (applied to the gradient and hessian)."""
    if aug:
        Fall = np.vstack([FF, _orig_aug(FF, names, share=aug_share, seed=seed + 1)]); rr_ = np.concatenate([ri, ri + nR])
        tr = np.concatenate([train_races, train_races + nR]); t = np.concatenate([target, target])
        w = None if weight is None else np.concatenate([weight, weight])
    else:
        Fall, rr_, tr, t, w = FF, ri, train_races, target, weight
    m = np.isin(rr_, tr); _, rr = np.unique(rr_[m], return_inverse=True); n = rr.max() + 1
    P = dict(learning_rate=0.06, num_leaves=15, min_data_in_leaf=100, feature_fraction=0.2, extra_trees=True, bagging_fraction=0.8,
             bagging_freq=1, lambda_l2=10.0, verbose=-1, objective="none", num_threads=4, seed=seed)
    if params: P.update(params)
    tm = t[m]; wm = None if w is None else w[m]

    def fobj(preds, ds):
        p = gbm.race_softmax(preds, rr, n); g, h = p - tm, np.maximum(p * (1 - p), 1e-6)
        return (g, h) if wm is None else (g * wm, h * wm)
    bst = lgb.Booster(params=P, train_set=lgb.Dataset(Fall[m]))
    for _ in range(rounds): bst.update(fobj=fobj)
    return bst


def fit(FF, names, fold, seeds=(0, 1, 2), target=None, **kw):
    train_races = np.arange(nR)[rdate < FOLDS[fold][0]]; preds, last = [], None
    for s in seeds:
        last = train(FF, names, train_races, q if target is None else target, seed=s, **kw)
        preds.append(np.log(b.softmax_races(last.predict(FF))))
    return b.softmax_races(np.mean(preds, 0)), last


def kl(p, hm):
    hri = np.unique(ri[hm], return_inverse=True)[1]; nh = hri.max() + 1; qh = q[hm]; ph = p[hm]
    ok = np.bincount(hri, weights=(qh > 0), minlength=nh) == np.bincount(hri, minlength=nh); m = ok[hri]
    return float(np.sum(np.where(qh[m] > 0, qh[m] * np.log(np.maximum(qh[m], 1e-300) / np.maximum(ph[m], 1e-12)), 0)) / ok.sum())


def ll(p, hm):
    m = hm & won; return float(-np.mean(np.log(np.maximum(p[m], 1e-12))))


def run(pm, hm, edge=1.2, lo=1.6, hi=15.0, ceil=3.0, tiers=TIERS, price=None, ded=DED):
    """The live BetMatic rules at Form King's open: bets, winners, staked, profit."""
    price = o if price is None else price
    base = hm & race_ok[ri] & np.isfinite(bs) & (pm > 0); qq = 1 / np.maximum(pm, 1e-9)
    mo = 0.95 * (edge / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78); n = st = pl = w = 0
    for i in np.where(base & (qq >= lo) & (qq <= hi) & (price >= mo) & (price < ceil * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in tiers if mo[i] * s < ceil * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp, only[i], field[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if price[i] >= t: tot += add
        if tot > 0:
            n += 1; st += tot; w += won[i]; pl += tot * (price[i] - 1) * (1 - ded) if won[i] else -tot
    return n, int(w), float(st), float(pl)


def score(p, fold):
    out = {}
    for name, lo, hi in PERIODS[fold]:
        hm = (date >= lo) & (date < hi); n, w, st, pl = run(p, hm)
        out[name] = dict(kl=kl(p, hm), ll=ll(p, hm), bets=n, won=w, staked=st, profit=pl)
    return out


def done(name, fold, path="results.jsonl"):
    if not os.path.exists(path): return False
    return any((j := json.loads(l))["name"] == name and j["fold"] == fold for l in open(path) if l.strip())


def record(name, fold, p, note="", extra=None, path="results.jsonl"):
    sc = score(p, fold); np.save(f"preds/{name}_{fold}.npy", p.astype(np.float32))
    open(path, "a").write(json.dumps(dict(name=name, fold=fold, note=note, score=sc, extra=extra or {}, t=time.strftime("%H:%M"))) + "\n")
    a = sc[PERIODS[fold][2][0]]
    print(f"{time.strftime('%H:%M')} {name:28s} {fold}  KL {a['kl']:.4f}  LL {a['ll']:.4f}  bets {a['bets']}  profit {a['profit']:+.1f}u  | "
          + "  ".join(f"{k.split()[0]} {v['kl']:.4f}/{v['ll']:.4f}/{v['profit']:+.0f}u" for k, v in list(sc.items())[:2]), flush=True)
    return sc
