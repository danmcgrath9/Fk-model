"""Calibration by segment and uncertainty-scaled stakes (1 Nov 2026, founder: "Yeah nice" to a weekly calibration check and
cutting stakes where the model is less sure). Holdout from 3 Jun 2026 (v10 never trained on it), the live open rule as in
t_track_profit.py. Flags: metro, wet (soft or heavy: going band 2-3; 1 good, 4 synthetic), first up (90+ days), lightly raced (<=3 starts), thin speed data."""
import numpy as np, collections, json, stake_rule
z = np.load("ds/model_ds_v10.npz", allow_pickle=True)
ri = z["race_idx"]; nR = int(ri.max()) + 1
p10 = np.load("v10_profit_preds.npz")["p10"].astype(float)
o = z["open"].astype(float); bs = z["bsp"].astype(float); won = z["finish"] == 1; rdate = z["date"].astype(str)
trk = z["track"].astype(str); going = z["going"].astype(float); cols = list(z["cols"]); X = z["X"]
col = lambda n: X[:, cols.index(n)].astype(float)
days = col("daysSinceLastRace"); starts = np.expm1(col("raw_starts")) if False else col("raw_starts")
P = z["P"]; pf = list(z["past_fields"]); spd = P[:, :, pf.index("speedRating")]; db = P[:, :, pf.index("days_before")]
n_spd = (np.isfinite(spd) & (spd != 0) & np.isfinite(db)).sum(1)
okr = np.isfinite(bs) & (bs > 1) & np.isfinite(p10) & (p10 > 0) & np.isfinite(o) & (o > 1)
cnt = np.bincount(ri, minlength=nR)
race_ok = (np.bincount(ri, weights=okr.astype(float), minlength=nR) == cnt) & (rdate >= "2026-06-03") & \
          (np.bincount(ri, weights=won.astype(float), minlength=nR) >= 1)
m = race_ok[ri]
s = np.bincount(ri, weights=np.where(m, p10, 0), minlength=nR); pm = np.where(m, p10 / np.where(s[ri] > 0, s[ri], 1), np.nan)
ib = np.where(m, 1 / bs, 0); sb = np.bincount(ri, weights=ib, minlength=nR); pb = np.where(m, ib / np.where(sb[ri] > 0, sb[ri], 1), np.nan)
clean = lambda t: [t := t.replace(x, "") for x in (" Synthetic", " Hillside", " Lakeside", " Heath", " Park", " Poly")][-1].strip()
metro = {"Flemington", "Caulfield", "Moonee Valley", "Sandown"}
is_metro = np.array([clean(trk[r]) in metro for r in ri])
print("raw_starts sample", np.nanpercentile(starts[m], [5, 25, 50, 75]), "days", np.nanpercentile(days[m], [5, 50, 95]), "n_spd", np.bincount(n_spd[m]))
FL = {"metro": is_metro, "wet": np.isin(going[ri], (2.0, 3.0)), "first_up": days >= 90, "light": starts <= 3, "thin_speed": n_spd <= 2}
# ---- calibration, every holdout runner ----
def cal(mask):
    w = won[mask].sum(); e = pm[mask].sum(); eb = pb[mask].sum(); n = mask.sum()
    return n, int(w), e, eb
print("\nCALIBRATION, all holdout runners: actual wins / model-expected / market(BSP)-expected")
bands = [(1, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 20), (20, 1e9)]
for name, seg in [("ALL", m)] + [(k, m & v) for k, v in FL.items()] + [("country/prov", m & ~is_metro)]:
    n, w, e, eb = cal(seg); print(f"{name:12s} n={n:5d} won {w:4d}  model {e:7.1f} ({w/e:4.2f})  market {eb:7.1f} ({w/eb:4.2f})")
print("\nby our price band (all / metro / wet)")
for lo, hi in bands:
    q = 1 / np.where(m, pm, np.nan); b = m & (q >= lo) & (q < hi)
    row = []
    for seg in (b, b & is_metro, b & np.isin(going[ri], (2.0, 3.0))):
        n, w, e, eb = cal(seg); row.append(f"{w:4d}/{e:6.1f} ({w/e if e else 0:4.2f})")
    print(f"${lo:>4}-{hi if hi < 1e8 else 'up':<4}", "  ".join(row))
# ---- bets under the live rule ----
B = []
for i in np.where(m)[0]:
    q = 1 / pm[i]
    if not (1.6 <= q <= 15 and o[i] < 3 * q): continue
    E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pm[i] ** 0.82) ** (1 / 0.78)
    if o[i] < mo: continue
    tiers = [mo * x for x in (1.0, 1.25, 1.5) if mo * x < 3 * q]; tot = prev = 0.0
    for k, tt in enumerate(tiers):
        tp = tiers[k + 1] if k + 1 < len(tiers) else tt
        s_ = stake_rule.stake(pm[i] ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if o[i] >= tt: tot += add
    if tot > 0: B.append((i, tot))
idx = np.array([b[0] for b in B]); st = np.array([b[1] for b in B])
plo = np.where(won[idx], (o[idx] - 1) * 0.93, -1.0); plb = np.where(won[idx], (bs[idx] - 1) * 0.92, -1.0)
beat = o[idx] > bs[idx]
order = np.argsort(rdate[ri[idx]], kind="stable")
print(f"\nBETS (live open rule): {len(idx)}, {st.sum():.0f}u, open {np.dot(st, plo):+.0f}u ({100*np.dot(st, plo)/st.sum():+.1f}%), BSP {np.dot(st, plb):+.0f}u")
print(f"{'flag':12s} {'bets':>5s} {'units':>7s} {'P/L open':>9s} {'ROI':>6s} {'ROI BSP':>8s} {'won/exp':>10s} {'beat BSP':>8s}")
res = {}
for k, v in [("none", ~np.any([f[idx] for f in FL.values()], axis=0))] + [(k, f[idx]) for k, f in FL.items()]:
    a = v; u = st[a].sum(); po = np.dot(st[a], plo[a]); pbp = np.dot(st[a], plb[a])
    res[k] = dict(bets=int(a.sum()), units=round(u, 1), pl_open=round(po, 1), roi_open=round(100 * po / u, 1), roi_bsp=round(100 * pbp / u, 1),
                  won=int(won[idx][a].sum()), exp=round(pm[idx][a].sum(), 1), beat_bsp=round(100 * beat[a].mean(), 1))
    r = res[k]; print(f"{k:12s} {r['bets']:5d} {u:7.0f} {po:+9.0f} {r['roi_open']:+5.1f}% {r['roi_bsp']:+7.1f}% {r['won']:4d}/{r['exp']:5.1f} {r['beat_bsp']:7.1f}%")
def run(mult):
    s2 = st * mult; pl = s2 * plo; c = np.cumsum(pl[order]); dd = np.max(np.maximum.accumulate(c) - c)
    mon = collections.Counter()
    for j, x in zip(rdate[ri[idx]], pl): mon[j[:7]] += x
    return s2.sum(), pl.sum(), dd, min(mon.values())
print(f"\nSTAKE CUTS: {'scheme':34s} {'units':>7s} {'P/L':>7s} {'ROI':>6s} {'worst DD':>8s} {'worst mth':>9s}")
schemes = {"live (metro already half on sheets)": np.ones(len(idx))}
for k in FL: schemes[f"half when {k}"] = np.where(FL[k][idx], 0.5, 1.0)
anyunc = np.any([FL[k][idx] for k in ("wet", "first_up", "light", "thin_speed")], axis=0)
schemes["half when any non-metro flag"] = np.where(anyunc, 0.5, 1.0)
nfl = np.sum([FL[k][idx] for k in ("wet", "first_up", "light", "thin_speed")], axis=0)
schemes["x0.75 per flag"] = 0.75 ** nfl
for k, mult in schemes.items():
    u, pl, dd, wm = run(mult); print(f"{k:46s} {u:7.0f} {pl:+7.0f} {100*pl/u:+5.1f}% {dd:8.0f} {wm:+9.0f}")
json.dump(res, open("calib_unc.json", "w"), indent=1)
# ---- the weekly check, replayed: each Sunday, bets in the trailing 8 weeks, actual v expected wins per segment ----
bd = rdate[ri[idx]]; pe = pm[idx]; wn = won[idx]
segs = {"all": np.ones(len(idx), bool), **{k: FL[k][idx] for k in FL}, "country/prov": ~FL["metro"][idx]}
import datetime as dt
d0 = dt.date(2026, 7, 5); print("\nWEEKLY CHECK (trailing 8 weeks of bets): segments flagged when wins sit 2 SD under the model")
first = {}
while d0 <= dt.date.fromisoformat(max(bd)):
    lo = (d0 - dt.timedelta(days=56)).isoformat(); hi = d0.isoformat(); w8 = (bd > lo) & (bd <= hi); out = []
    for k, sm in segs.items():
        a = w8 & sm; e = pe[a].sum(); w = wn[a].sum(); sd = np.sqrt((pe[a] * (1 - pe[a])).sum())
        if e >= 15 and (w - e) / sd <= -2: out.append(f"{k} {w}/{e:.0f}"); first.setdefault(k, hi)
    print(hi, ", ".join(out) or "ok")
    d0 += dt.timedelta(days=7)
print("first flagged:", first, "last bet", max(bd))
