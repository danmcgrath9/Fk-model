"""Stage 3: one calibration layer over everything we have found (1 Nov 2026, founder: "use any inputs like the details we
have been rolling to get closer to BSP and winning ROI"). A logistic model over the out-of-fold log-odds plus the context
the stage-1 trees cannot see as context: metro, Flemington straight, settle style, run in prep, came back better/worse,
first starters in the race, field size, distance band, going, the open price band, the model-v-open gap, the jockey
undeclared flag. Fitted on the first date half, scored on the second (then swapped): KL to BSP, winner log loss and the
open-rule plan's ROI, against the raw out-of-fold chance. Then the same with the OPEN price as an input (the market blend
done per context rather than one weight for every runner)."""
import numpy as np, stake_rule, prep_feats
from sklearn.linear_model import LogisticRegression
z = np.load("ds/model_ds.npz", allow_pickle=True); p = np.load("p_oof_blend9.npy").astype(float)
ri = z["race_idx"]; nR = int(ri.max()) + 1; won = z["finish"] == 1; bs = z["bsp"].astype(float); o = z["open"].astype(float)
cols = [str(c) for c in z["cols"]]; X = z["X"].astype(float); cnt = np.bincount(ri, minlength=nR); fld = cnt[ri].astype(float)
ok = np.isfinite(p) & (p > 0) & np.isfinite(bs) & (bs > 1) & np.isfinite(o) & (o > 1)
race_ok = (np.bincount(ri, weights=ok.astype(float), minlength=nR) == cnt) & (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1); m = race_ok[ri]
nrm = lambda v: np.where(m, v / np.where(np.bincount(ri, weights=np.where(m, v, 0), minlength=nR)[ri] > 0, np.bincount(ri, weights=np.where(m, v, 0), minlength=nR)[ri], 1), np.nan)
pm = nrm(p); qb = nrm(np.where(m, 1 / bs, 0)); qo = nrm(np.where(m, 1 / o, 0))
trk = z["track"].astype(str)[ri]; dist = z["distance"].astype(float)[ri]; going = z["going"].astype(float)[ri]; d = z["date"].astype(str)[ri]
base = lambda t: t.replace(" Synthetic","").replace(" Hillside","").replace(" Lakeside","").replace(" Heath","").replace(" Park","").strip()
bt = np.array([base(t) for t in trk]); metro = np.isin(bt, ["Flemington", "Caulfield", "Moonee Valley", "Sandown"]); straight = (bt == "Flemington") & (dist <= 1200)
ss = X[:, cols.index("raw_settle_share")]; rip = X[:, cols.index("raw_run_in_prep")]; fs = X[:, cols.index("firstStarter")] == 1
nfs = np.bincount(ri, weights=fs.astype(float), minlength=nR)[ri]; jk = z["jockey"].astype(str); und = np.array([j.strip() == "" for j in jk])
F = prep_feats.build(z["P"], list(z["past_fields"]), rip); fg = np.nan_to_num(F["fu_gain"], nan=0.0); fg_set = np.isfinite(F["fu_gain"]).astype(float)
lo = np.log(np.clip(pm, 1e-6, 1 - 1e-6) / (1 - np.clip(pm, 1e-6, 1 - 1e-6))); lo_o = np.log(np.clip(qo, 1e-6, 1 - 1e-6) / (1 - np.clip(qo, 1e-6, 1 - 1e-6)))
ssn = np.nan_to_num(ss, nan=0.45); fwd = (ssn < 0.3).astype(float); back = (ssn >= 0.65).astype(float)
ctx = {"metro": metro.astype(float), "metro_x_lo": metro * lo, "straight": straight.astype(float), "straight_fwd": straight * fwd, "straight_back": straight * back,
       "fwd": fwd, "back": back, "back_x_dist": back * (dist > 1200), "first_up": (rip == 1).astype(float), "second_up": (rip == 2).astype(float),
       "fu_gain": fg / 10, "fu_gain_set": fg_set, "fs_in_race": (nfs > 0).astype(float), "n_fs": nfs / 5, "field": fld / 14, "sprint": (dist <= 1200).astype(float),
       "staying": (dist >= 2000).astype(float), "wet": np.isin(going, (2.0, 3.0)).astype(float), "synthetic": (going == 4.0).astype(float),
       "lo_x_short": lo * (o < 5), "lo_x_long": lo * (o >= 12), "gap": lo - lo_o, "gap_x_metro": (lo - lo_o) * metro, "undeclared": und.astype(float)}
def design(with_open):
    A = [lo] + ([lo_o] if with_open else []) + list(ctx.values()); return np.column_stack(A)
def kl(pp, sel): v = np.bincount(ri, weights=np.where(sel, qb * np.log(np.maximum(qb, 1e-12) / np.maximum(pp, 1e-12)), 0), minlength=nR); rs = np.zeros(nR, bool); rs[np.unique(ri[sel])] = True; return v[rs].mean()
def ll(pp, sel): return -np.log(pp[sel & won]).mean()
def plan(pp, sel):
    out = []
    for i in np.where(sel)[0]:
        q = 1 / pp[i]
        if not (1.6 <= q <= 15 and o[i] < 3 * q) or (metro[i] and o[i] >= 12): continue
        E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pp[i] ** 0.82) ** (1 / 0.78)
        if o[i] >= mo: out.append((i, stake_rule.stake(pp[i] ** 0.82 * o[i] ** -0.22, o[i])))
    idx = np.array([i for i, _ in out]); st = np.array([s for _, s in out]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st); plb = np.where(won[idx], st * (bs[idx] - 1) * 0.92, -st)
    return len(idx), st.sum(), pl.sum(), 100 * pl.sum() / st.sum(), 100 * plb.sum() / st.sum()
cut = "2026-02-15"; halves = [(d < cut, d >= cut), (d >= cut, d < cut)]
for with_open in (False, True):
    A = design(with_open); A[~np.isfinite(A)] = 0
    pp = np.full(len(pm), np.nan)
    for tr, te in halves:
        mdl = LogisticRegression(C=1.0, max_iter=2000); mdl.fit(A[m & tr], won[m & tr]); pp[m & te] = mdl.predict_proba(A[m & te])[:, 1]
        if not with_open and tr[0]:
            names = ["model_logodds"] + list(ctx); print("  fitted weights (first half):", ", ".join(f"{n} {w:+.2f}" for n, w in zip(names, mdl.coef_[0]) if abs(w) >= 0.05))
    pp = nrm(np.where(m, pp, 0))
    print(f"\n{'WITH the open price as an input' if with_open else 'CONTEXT ONLY (no market)'}")
    for lab, pq in (("raw out-of-fold model", pm), ("stage 3", pp)):
        n, st, pl, roi, roib = plan(pq, m)
        print(f"  {lab:22s} KL to BSP {kl(pq, m):.4f}  winner log loss {ll(pq, m):.4f}  plan {n:5d} bets {st:6.0f}u {pl:+6.0f}u ({roi:+5.1f}% open, {roib:+5.1f}% BSP)")
        for hl, (tr, te) in zip(("first half", "second half"), halves):
            n, st, pl, roi, roib = plan(pq, m & te); print(f"      {hl:12s} KL {kl(pq, m & te):.4f}  plan {n:5d} bets {pl:+6.0f}u ({roi:+5.1f}% open, {roib:+5.1f}% BSP)")
# variants (1 Nov, second pass): no market inputs at all; and the race-shape flags only. Plus worst drawdown.
def run_variant(lab, keys):
    A = np.column_stack([lo] + [ctx[k] for k in keys]); A[~np.isfinite(A)] = 0; pp = np.full(len(pm), np.nan)
    for tr, te in halves:
        mdl = LogisticRegression(C=1.0, max_iter=2000); mdl.fit(A[m & tr], won[m & tr]); pp[m & te] = mdl.predict_proba(A[m & te])[:, 1]
    pp = nrm(np.where(m, pp, 0)); n, st, pl, roi, roib = plan(pp, m)
    # drawdown
    out = []
    for i in np.where(m)[0]:
        q = 1 / pp[i]
        if not (1.6 <= q <= 15 and o[i] < 3 * q) or (metro[i] and o[i] >= 12): continue
        E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pp[i] ** 0.82) ** (1 / 0.78)
        if o[i] >= mo: out.append((i, stake_rule.stake(pp[i] ** 0.82 * o[i] ** -0.22, o[i])))
    idx = np.array([i for i, _ in out]); st_ = np.array([s for _, s in out]); od = np.argsort(d[idx], kind="stable"); plx = np.where(won[idx], st_ * (o[idx] - 1) * 0.93, -st_)[od]; c = np.cumsum(plx)
    print(f"  {lab:34s} KL {kl(pp, m):.4f}  plan {n:5d} bets {st:6.0f}u {pl:+6.0f}u ({roi:+5.1f}% open, {roib:+5.1f}% BSP)  worst DD {np.max(np.maximum.accumulate(c)-c):.0f}u")
    return pp
print("\nVARIANTS")
_ = run_variant("raw model (reference)", [])
nomkt = [k for k in ctx if k not in ("gap", "gap_x_metro", "lo_x_short", "lo_x_long")]
pp_nomkt = run_variant("stage 3, no market inputs", nomkt)
pp_shape = run_variant("race shape only (metro/straight/style)", ["metro", "metro_x_lo", "straight", "straight_fwd", "straight_back", "fwd", "back", "back_x_dist", "field"])
np.save("p_stage3_nomkt.npy", pp_nomkt)
