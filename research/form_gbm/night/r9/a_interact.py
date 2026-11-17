"""a_interact.py: does our price deserve more weight at 9am in some races than others? (18 Nov 2026)
Base: ours + median majors + move (walk-forward). One interaction at a time: our price's weight allowed to differ in
metro races, big fields, 2yo/maiden-type races (first starters in the race), wet tracks, and by time to the jump."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
first = np.array([p_[1][0] if p_ is not None else np.nan for p_ in tab])
n7 = np.isfinite(B7).sum(1)
ok = race_ok((P > 0) & np.isfinite(T9) & (T9 > 1) & (n7 >= 4) & np.isfinite(first) & (first > 1))
L = lambda x: np.log(np.where(ok & np.isfinite(x) & (x > 0), x, 1.0))
lo, lm, mv = L(P), -L(MED7), L(T9) - L(first)
fsz = np.bincount(ri, weights=ok, minlength=nR)[ri]
nfs = np.bincount(ri, weights=fs, minlength=nR)[ri]
X0 = z["X"]; g = lambda c: np.concatenate([X0[:, cols.index(c)], np.zeros(ng)]) if c in cols else None
hrs = -nine / 60
SEG = {"metro": metro, "field of 12+": fsz >= 12, "a first starter in the race": nfs > 0, "jumps within 6 h of 9am": hrs < 6, "jumps 8 h+ after 9am": hrs >= 8,
       "market favourite (median under $4)": MED7 < 4, "median $8+": MED7 >= 8}
for c in ("going_gap", "prize_log", "field_strength"):
    v = g(c)
    if v is not None: SEG[f"{c} above its median"] = v > np.nanmedian(v[:n0])
months = sorted(set(month[ok])); test = np.isin(month, months[4:]) & ok
def wf(X):
    p = np.zeros(n)
    for mo in months[4:]:
        b = fit_cl(X, ok & (month < mo)); te = ok & (month == mo); p[te] = softmax_by_race(X @ b, ok)[te]
    return p, b
p0, b0 = wf(np.column_stack([lo, lm, mv])); ll0 = logloss(p0, test)
print(f"base: ours {b0[0]:+.2f}, median {b0[1]:+.2f}, move {b0[2]:+.2f}; test log loss {ll0:.4f}\n")
print("| our price's weight allowed to differ in | share of runners | extra weight there (last fit) | test log loss change | per-race t |\n|---|---|---|---|---|")
w = test & won
for lab, m in SEG.items():
    m = np.asarray(m, bool) & ok
    p1, b1 = wf(np.column_stack([lo, lm, mv, lo * m])); d = np.log(p1[w]) - np.log(p0[w])
    print(f"| {lab} | {m[ok].mean():.0%} | {b1[3]:+.2f} | {logloss(p1, test) - ll0:+.4f} | {d.mean() / (d.std() / np.sqrt(len(d))):+.1f} |", flush=True)
