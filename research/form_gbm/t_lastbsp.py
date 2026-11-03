"""Does the market's own past price for a horse, and the lightly-raced-winner profile, improve our price? (3 Nov 2026,
founder: "Do all the testing like that", after Ranarsson.) v10 holdout 3 Jun - 13 Oct. A small logistic model on top of
our price: logit(win) = a + b*logit(ours) + c*logit(last-start BSP chance) + d*(won last start, 1-3 starts) + ...,
cross-fitted by date halves (fit on one, score the other), probabilities renormalised within the race. Measured on
log loss over every runner and on the live book (every live rule) at the open less 7%."""
import numpy as np
src = open("t_all_rules.py").read().split('summ(plan(pm0), "all rules')[0]
exec(src)
X = z["X"]; cols = list(map(str, z["cols"])); col = lambda c: X[:, cols.index(c)].astype(float)
pf = list(map(str, z["past_fields"])); P = z["P"]; FIN, BSPF, TRI = pf.index("finish"), pf.index("bsp"), pf.index("trial")
n = len(pmS)
q_last = np.full(n, np.nan); won_last = np.zeros(n); runs_back = np.full(n, np.nan)
for i in range(n):
    for r in range(P.shape[1]):
        if np.isfinite(P[i, r, FIN]) and P[i, r, TRI] == 0:   # most recent RACE (trials carry no price)
            bb = P[i, r, BSPF]
            if np.isfinite(bb) and bb > 1: q_last[i] = 1 / bb
            won_last[i] = float(P[i, r, FIN] == 1); runs_back[i] = r; break
starts = col("raw_starts"); lrw = ((won_last == 1) & (starts <= 3)).astype(float)
ok = m & np.isfinite(pmS) & (pmS > 0) & (pmS < 1)
lg = lambda p: np.log(p / (1 - p))
def design(ii):
    ql = q_last[ii]; miss = ~np.isfinite(ql); qq = np.where(miss, 0.1, ql)
    return np.column_stack([np.ones(len(ii)), lg(pmS[ii]), np.where(miss, 0.0, lg(qq) - lg(pmS[ii])), miss.astype(float), lrw[ii], won_last[ii]])
NAMES = ["intercept", "logit(ours)", "logit(last BSP) - logit(ours)", "no last-start price", "won last, 1-3 starts", "won last start"]
def fit(A, y, l2=1.0):
    w = np.zeros(A.shape[1])
    for _ in range(25):
        p = 1 / (1 + np.exp(-A @ w)); g = A.T @ (p - y) + l2 * w * (np.arange(len(w)) > 1)
        H = (A * (p * (1 - p))[:, None]).T @ A + l2 * np.eye(len(w)) * (np.arange(len(w)) > 1); w -= np.linalg.solve(H, g)
    return w
H1 = dd < "2026-08-01"
p_new = np.full(n, np.nan)
for fit_on, score_on, lab in ((H1, ~H1, "fit Jun-Jul, score Aug-Oct"), (~H1, H1, "fit Aug-Oct, score Jun-Jul")):
    a = np.where(ok & fit_on)[0]; b = np.where(ok & score_on)[0]
    w = fit(design(a), won[a].astype(float)); print(f"{lab}: " + ", ".join(f"{k} {v:+.2f}" for k, v in zip(NAMES, w)))
    p_new[b] = 1 / (1 + np.exp(-(design(b) @ w)))
pN = norm(np.where(np.isfinite(p_new), p_new, 0))
ll = lambda p, ii: -np.mean(np.where(won[ii], np.log(p[ii]), np.log(1 - p[ii])))
ii = np.where(ok)[0]
print(f"\nlog loss, every runner (lower is better): ours {ll(pmS, ii):.4f}  with last-start BSP + profile {ll(pN, ii):.4f}  "
      f"(Jun-Jul {ll(pmS, ii[H1[ii]]):.4f} -> {ll(pN, ii[H1[ii]]):.4f}; Aug-Oct {ll(pmS, ii[~H1[ii]]):.4f} -> {ll(pN, ii[~H1[ii]]):.4f})")
k = ok & (lrw == 1); print(f"lightly raced last-start winners: {k.sum()} runners, median price ours ${np.median(1/pmS[k]):.2f} -> ${np.median(1/pN[k]):.2f}")
k = ok & np.isfinite(q_last) & (q_last > 0.4); print(f"horses the market had under $2.50 last start: {k.sum()}, median ours ${np.median(1/pmS[k]):.2f} -> ${np.median(1/pN[k]):.2f}; "
      f"won {won[k].sum()} v ours {pmS[k].sum():.1f} v new {pN[k].sum():.1f}")
def book(p, lab):
    b = plan(p); idx = np.array([i for i, _ in b]); st = np.array([s for _, s in b]); od = np.argsort(dd[idx], kind="stable"); idx, st = idx[od], st[od]
    pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); plb = np.where(won[idx], st * (bs[idx] - 1) * 0.92, -st); h1 = dd[idx] < "2026-08-01"
    c = np.cumsum(pl); D = np.max(np.maximum.accumulate(c) - c)
    print(f"{lab:34s} {len(idx):5d} bets {won[idx].sum():4d} won {st.sum():6.0f}u {pl.sum():+6.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  halves {100*pl[h1].sum()/st[h1].sum():+3.0f}%/{100*pl[~h1].sum()/st[~h1].sum():+3.0f}%  DD {D:3.0f}u  BSP {100*plb.sum()/st.sum():+4.0f}%")
    return set(idx)
print("\nTHE LIVE BOOK (every live rule, open less 7%):")
s0 = book(pmS, "ours as live"); s1 = book(pN, "with last-start BSP + profile")
print(f"bets in both {len(s0 & s1)}, dropped {len(s0 - s1)}, added {len(s1 - s0)}")
# the profile on its own: a flat uplift to the chance of lightly raced last-start winners
for up in (1.10, 1.15, 1.20):
    pU = norm(np.where(ok, pmS * np.where(lrw == 1, up, 1.0), 0)); book(pU, f"ours x{up:g} on lightly raced winners")
