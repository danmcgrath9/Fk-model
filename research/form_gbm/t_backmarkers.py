"""Backmarkers (1 Nov 2026, founder: "backmarkers down the straight versus a bend? Or backmarkers in sprint races versus
middle distance"). Full history Jul 2025 - Oct 2026 on out-of-fold predictions. Run style from Form King's predicted settling
position (known before the race): leader, on pace (front third), midfield, back (back third). Wins v the model (before the
live back-settler shade) and v the market."""
import numpy as np, stake_rule
exec(open("t_straight_oof.py").read().split("def row(")[0])
pos = z["X"][:, cols.index("sm_predicted_position")].astype(float); ps = (pos - 1) / np.maximum(fld - 1, 1)
style = np.where(np.isnan(pos), "", np.where(pos == 1, "leader", np.where(ps < 1/3, "on pace", np.where(ps < 2/3, "midfield", "back"))))
def row(lab, g):
    g = g & m; w = won[g].sum(); e = pm[g].sum(); eb = pb[g].sum(); sd = np.sqrt((pm[g] * (1 - pm[g])).sum())
    if g.sum() >= 30: print(f"  {lab:34s} runners {g.sum():5d} won {w:4d}  model {e:6.1f} ({w/e:4.2f}, z {(w-e)/sd:+.1f})  market {eb:6.1f} ({w/eb:4.2f})")
groups = [("Flemington straight", straight), ("bend sprints <=1200m", bend),
          ("1300-1800m", (dist > 1200) & (dist <= 1800)), ("2000m+", dist >= 2000)]
for lab, g in groups:
    print(lab)
    for s in ("leader", "on pace", "midfield", "back"): row(f"  {s}", g & (style == s))
# our value bets (open rule, no shade, full stakes at the open, $1.60-$15, under 3x ours) by settle style and distance
ss = z["X"][:, cols.index("raw_settle_share")].astype(float)
B = []
for i in np.where(m)[0]:
    q = 1 / pm[i]
    if not (1.6 <= q <= 15 and np.isfinite(o[i]) and o[i] < 3 * q): continue
    E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pm[i] ** 0.82) ** (1 / 0.78)
    if o[i] >= mo: B.append((i, stake_rule.stake(pm[i] ** 0.82 * o[i] ** -0.22, o[i])))
idx = np.array([i for i, _ in B]); st = np.array([s for _, s in B]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
sty = np.where(np.isnan(ss[idx]), "?", np.where(ss[idx] < .3, "forward", np.where(ss[idx] < .65, "midfield", "back")))
print("\nOUR BETS (no shade): wins / model expected, ROI at the open less 7%")
for lab, g in (("Flemington straight", straight[idx]), ("bend sprints <=1200m", bend[idx]), ("1300-1800m", ((dist > 1200) & (dist <= 1800))[idx]), ("2000m+", (dist >= 2000)[idx])):
    print(lab)
    for s in ("forward", "midfield", "back"):
        k = g & (sty == s)
        if k.sum() >= 10: print(f"    {s:9s} bets {k.sum():4d} won {won[idx][k].sum():3d}/{pm[idx][k].sum():5.1f} ({won[idx][k].sum()/pm[idx][k].sum():4.2f})  {pl[k].sum():+7.1f}u ({100*pl[k].sum()/st[k].sum():+5.1f}%)")
# shade schemes: x0.85 on back-settlers (settle share 0.65+), race renormalised, then the open rule
def with_shade(sel):
    q = np.where(m & sel & (ss >= 0.65), pm * 0.85, pm); s_ = np.bincount(ri, weights=np.where(m, q, 0), minlength=nR); return np.where(m, q / np.where(s_[ri] > 0, s_[ri], 1), np.nan)
def plan(pp):
    out = []
    for i in np.where(m)[0]:
        q = 1 / pp[i]
        if not (1.6 <= q <= 15 and np.isfinite(o[i]) and o[i] < 3 * q): continue
        E = 1.15 if q < 4 else 1.2; mo = 0.95 * (E / pp[i] ** 0.82) ** (1 / 0.78)
        if o[i] >= mo: out.append((i, stake_rule.stake(pp[i] ** 0.82 * o[i] ** -0.22, o[i])))
    idx = np.array([i for i, _ in out]); st = np.array([s for _, s in out]); pl = np.where(won[idx], st * (o[idx] - 1) * 0.93, -st)
    dd_ = z["date"].astype(str)[ri][idx]; h1 = dd_ < "2026-02-15"
    return f"{len(idx):5d} bets {st.sum():7.0f}u {pl.sum():+8.0f}u ({100*pl.sum()/st.sum():+5.1f}%)  halves {100*pl[h1].sum()/st[h1].sum():+5.1f}% / {100*pl[~h1].sum()/st[~h1].sum():+5.1f}%"
print("\nSHADE SCHEMES (full history, out of fold)")
print("  no shade                          ", plan(pm))
print("  shade every back-settler (live)   ", plan(with_shade(np.ones(len(m), bool))))
print("  shade only beyond 1200m           ", plan(with_shade(dist > 1200)))
