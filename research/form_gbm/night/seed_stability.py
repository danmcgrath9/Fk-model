"""How much of the bet list is the network's seed? (night of 10 Nov 2026; reads queue 5's 20 network seeds)
The full live blend priced twice with two different draws of network seeds, everything else the same. The live rules at
Form King's open: which bets are in both lists, which in only one, and what each kind made.
    python3.13 seed_stability.py   (night folder, after queue5.py)"""
import numpy as np
import nl, stake_rule
sm_ = nl.b.softmax_races; L_ = lambda p: np.log(np.maximum(p, 1e-12)); avg = lambda ps: sm_(np.mean([L_(p) for p in ps], 0))
hm = {f: (nl.date >= nl.FOLDS[f][1]) & (nl.date < nl.FOLDS[f][2]) for f in "AB"}
ld = lambda n, f: np.load(f"preds/{n}_{f}.npy").astype(float)


def bets(pm, m, edge=1.2, lo=1.6, hi=15.0, ceil=3.0, tiers=nl.TIERS):
    """nl.run, returning each bet: runner -> (stake, profit)"""
    price = nl.o; base = m & nl.race_ok[nl.ri] & np.isfinite(nl.bs) & (pm > 0); qq = 1 / np.maximum(pm, 1e-9)
    mo = 0.95 * (edge / np.maximum(pm, 1e-9) ** 0.82) ** (1 / 0.78); out = {}
    for i in np.where(base & (qq >= lo) & (qq <= hi) & (price >= mo) & (price < ceil * qq))[0]:
        ch = lambda t: pm[i] ** 0.82 * t ** -0.22
        ts = [mo[i] * s for s in tiers if mo[i] * s < ceil * qq[i]]; tot = prev = 0.0
        for k, t in enumerate(ts):
            tp = ts[k + 1] if k + 1 < len(ts) else t
            s_ = stake_rule.stake(ch(tp), tp, nl.only[i], nl.field[i]); add = max(0.0, s_ - prev); prev = max(prev, s_)
            if price[i] >= t: tot += add
        if tot > 0: out[i] = (tot, tot * (price[i] - 1) * (1 - nl.DED) if nl.won[i] else -tot)
    return out


def line(lab_, B):
    st = sum(v[0] for v in B); pl = sum(v[1] for v in B)
    return f"{lab_}: {len(B)} bets, staked {st:.0f}u, {pl:+.0f}u ({100*pl/max(st,1e-9):+.0f}%)"


for n in (5, 10):
    print(f"\nTWO DRAWS OF {n} NETWORK SEEDS (trees 5 seeds, CatBoost 1 seed, live weights)")
    for f in "AB":
        NN = ld("m_nn20", f); t = sm_(0.7 * L_(ld("base5", f)) + 0.3 * L_(ld("m_rg", f))); cb = ld("m_cb", f)
        pa = sm_(0.5 * L_(t) + 0.3 * L_(avg(NN[:n])) + 0.2 * L_(cb)); pb = sm_(0.5 * L_(t) + 0.3 * L_(avg(NN[n:2 * n])) + 0.2 * L_(cb))
        A, B = bets(pa, hm[f]), bets(pb, hm[f]); both = set(A) & set(B); onlyA = set(A) - set(B); onlyB = set(B) - set(A)
        d = np.abs(np.log(pa[hm[f]] / pb[hm[f]])); ds = np.array([abs(A[i][0] - B[i][0]) / max(A[i][0], B[i][0]) for i in both])
        print(f"fold {f}: the two prices are a median {100*np.median(d):.1f}% apart (90th pct {100*np.percentile(d, 90):.1f}%); "
              f"{len(both)} bets in both lists, {len(onlyA)} only in the first, {len(onlyB)} only in the second "
              f"({100*len(both)/max(len(set(A)|set(B)),1):.0f}% shared); shared bets' stakes differ by a median {100*np.median(ds):.0f}%")
        print("  " + line("in both lists (first draw's stakes)", [A[i] for i in both]))
        print("  " + line("in one list only", [A[i] for i in onlyA] + [B[i] for i in onlyB]))
        print("  " + line("first draw, all", list(A.values())) + "   |   " + line("second draw, all", list(B.values())))
print("\nFor scale: the same lists from two 3-seed sets of the TREES (network 3 seeds, CatBoost 1)")
for f in "AB":
    def bl(name): t = sm_(0.7 * L_(ld(name, f)) + 0.3 * L_(ld("m_rg", f))); return sm_(0.5 * L_(t) + 0.3 * L_(ld("m_nn", f)) + 0.2 * L_(ld("m_cb", f)))
    pa, pb = bl("base"), bl("base_s10"); A, B = bets(pa, hm[f]), bets(pb, hm[f]); both = set(A) & set(B); one = [A[i] for i in set(A) - set(B)] + [B[i] for i in set(B) - set(A)]
    d = np.abs(np.log(pa[hm[f]] / pb[hm[f]]))
    print(f"fold {f}: prices a median {100*np.median(d):.1f}% apart; {len(both)} bets in both, {len(one)} in one only ({100*len(both)/max(len(set(A)|set(B)),1):.0f}% shared)")
    print("  " + line("in both", [A[i] for i in both])); print("  " + line("in one only", one))
