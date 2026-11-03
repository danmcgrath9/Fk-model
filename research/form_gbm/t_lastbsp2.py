"""Follow-up (3 Nov 2026): (1) was the "lightly raced last-start winner" uplift in t_plunge3.py a trial-counting bug?
(it took the most recent past run whether or not it was a trial); (2) does "the market had it under $2.50 / $3 last
start" add anything as a plain flag, cross-fitted by halves."""
import numpy as np
src = open("t_lastbsp.py").read().split("H1 = dd <")[0]
exec(src)
# (1) the profile, race-only against any-run (trials included)
first_any = np.array([next((P[i, r, FIN] for r in range(P.shape[1]) if np.isfinite(P[i, r, FIN])), np.nan) for i in range(n)])
A = np.where(ok & ~fs & (1/pmS >= 1.6) & (1/pmS <= 15))[0]
def ae(lab, k):
    ii = A[k[A]]; w = won[ii].sum(); e = pmS[ii].sum(); eb = (1/bs[ii]).sum(); h1 = dd[ii] < "2026-08-01"
    print(f"  {lab:52s} {len(ii):4d} runners {w:3d} won v ours {e:5.1f} (A/E {w/e:4.2f}) v BSP {eb:5.1f}; by half A/E {won[ii[h1]].sum()/pmS[ii[h1]].sum():4.2f} / {won[ii[~h1]].sum()/pmS[ii[~h1]].sum():4.2f}")
print("(1) lightly raced (1-3 starts) and won its most recent run:")
ae("most recent RACE was a win (trials skipped)", (won_last == 1) & (starts <= 3))
ae("most recent run of any kind was a win (t_plunge3's cut)", (first_any == 1) & (starts <= 3))
ae("most recent run was a TRIAL win, 1-3 starts", (first_any == 1) & (won_last != 1) & (starts <= 3))
ae("any 1-3 starts", starts <= 3)
print("(2) the market's price for the horse at its last race:")
for lo, hi, lab in ((0.4, 1.0, "under $2.50 last start"), (1/3, 0.4, "$2.50-$3"), (0.2, 1/3, "$3-$5"), (0.1, 0.2, "$5-$10"), (0.0, 0.1, "$10+")):
    ae(lab, np.isfinite(q_last) & (q_last > lo) & (q_last <= hi))
ae("under $2.50 last start AND ours $1.60-$4", np.isfinite(q_last) & (q_last > 0.4) & (1/pmS < 4))
ae("under $2.50 last start AND won it", np.isfinite(q_last) & (q_last > 0.4) & (won_last == 1))
ae("under $2.50 last start AND lost it", np.isfinite(q_last) & (q_last > 0.4) & (won_last == 0))
# cross-fitted flag model: ours + flag(under $2.50 last start)
H1 = dd < "2026-08-01"; flag = (np.isfinite(q_last) & (q_last > 0.4)).astype(float)
def des(ii): return np.column_stack([np.ones(len(ii)), lg(pmS[ii]), flag[ii]])
p_new = np.full(n, np.nan)
for fit_on, score_on, lab in ((H1, ~H1, "fit Jun-Jul"), (~H1, H1, "fit Aug-Oct")):
    a = np.where(ok & fit_on)[0]; b = np.where(ok & score_on)[0]; w = fit(des(a), won[a].astype(float)); p_new[b] = 1/(1+np.exp(-(des(b) @ w)))
    print(f"  {lab}: flag coefficient {w[2]:+.2f} (x{np.exp(w[2]):.2f} on the odds of winning)")
pN = norm(np.where(np.isfinite(p_new), p_new, 0)); ii = np.where(ok)[0]
print(f"  log loss ours {ll(pmS, ii):.4f} -> with the flag {ll(pN, ii):.4f}")
print("\nTHE LIVE BOOK:"); s0 = book(pmS, "ours as live"); s1 = book(pN, "with the under-$2.50-last-start flag")
