"""The firm/drift forecast on races it has never seen (night of 10 Nov 2026).
drift_forecast.py's model was trained on holdout races 6 May - 9 Oct and went live 19-21 Oct (stake x2 on the
forecast-to-firm third, x0.5 on the forecast-to-drift third); it fell out of the pipeline on 30 Oct when pricemtg.sh
replaced run_meeting.sh, and "put it back or retire it" has been waiting on the founder since 3 Nov.
Forward test: the committed LIVE prices (our price before the blend, each meeting's own file) on 15 Oct - 9 Nov, the
value bets under the live rule at Form King's open, each bet's forecast worked out at its own minimum odds exactly as the
order sheet does, thirds by the model's own stored cut points.
    python3.13 drift_live.py   (replay folder; models/drift_model.txt + drift_meta.json alongside)"""
import json, sys
import numpy as np
sys.path.insert(0, "/home/user/fk-model/research/form_gbm")
import drift_forecast as df, stake_rule
Z = np.load("ds/model_ds.npz", allow_pickle=True); LJ = np.load("live_join.npz")
ri = Z["race_idx"]; nR = len(Z["race_id"]); date = Z["date"].astype(str)[ri]; cols = list(Z["cols"])
bs = Z["bsp"].astype(float); o = Z["open"].astype(float); won = Z["finish"] == 1; fsr = Z["X"][:, cols.index("firstStarter")] == 1
field = np.bincount(ri, minlength=nR)[ri]
fc = df.Forecast("/home/user/fk-model/research/form_gbm/models"); ci = [cols.index(c) for c in fc.cols]
pm = LJ["p_model"]; ok = np.isfinite(pm) & (pm > 0) & np.isfinite(o) & (o > 1) & ~fsr & np.isfinite(bs)
v = np.where(ok & df.value_rows(np.nan_to_num(pm, nan=1e-9), np.nan_to_num(o, nan=0)))[0]
E = np.where(o[v] < 4, 1.15, 1.2); mo = 0.95 * (E / pm[v] ** 0.82) ** (1 / 0.78)
fz = fc.bst.predict(df.design(Z["X"][v][:, ci], pm[v], mo, field[v], [fc.book_for(int(f)) for f in field[v]]))
third = np.where(fz < fc.t1, 0, np.where(fz > fc.t2, 2, 1))
ch = pm[v] ** 0.82 * mo ** -0.22
st = np.array([stake_rule.stake(c, t) for c, t in zip(ch, mo)])
u_flat = np.where(won[v], (o[v] - 1) * 0.84, -1.0); u_st = u_flat * st; move = np.log(bs[v] / o[v])
print(f"live value bets 15 Oct - 9 Nov (committed prices, Form King's open, not first starters): {len(v)}; cut points {fc.t1:+.3f} / {fc.t2:+.3f}\n")
print("| forecast third | bets | won | flat 1u at the open | live stakes (first step) | median BSP/open | firmed |\n|---|---|---|---|---|---|---|")
for k, lab in enumerate(("forecast to DRIFT", "middle", "forecast to FIRM")):
    m = third == k
    print(f"| {lab} | {int(m.sum())} | {int(won[v][m].sum())} | {u_flat[m].sum():+.1f}u ({100*u_flat[m].mean():+.0f}%) | {u_st[m].sum():+.1f}u on {st[m].sum():.0f}u ({100*u_st[m].sum()/max(st[m].sum(),1e-9):+.0f}%) | {np.exp(np.median(move[m])):.2f} | {100*np.mean(move[m] < 0):.0f}% |")
print(f"| all | {len(v)} | {int(won[v].sum())} | {u_flat.sum():+.1f}u ({100*u_flat.mean():+.0f}%) | {u_st.sum():+.1f}u on {st.sum():.0f}u ({100*u_st.sum()/st.sum():+.0f}%) | {np.exp(np.median(move)):.2f} | {100*np.mean(move < 0):.0f}% |")
c = np.corrcoef(fz, -move)[0, 1]
print(f"\nforecast v the actual move (log open/BSP): correlation {c:+.2f} on {len(v)} bets (holdout, in-sample cross-fit: 0.27)")
half = np.array([d < "2026-10-29" for d in date[v]])
for lab, hm in (("15-28 Oct", half), ("29 Oct - 9 Nov", ~half)):
    print(f"  {lab}: " + "; ".join(f"{n} {int((hm & (third == k)).sum())} bets {u_flat[hm & (third == k)].sum():+.1f}u" for k, n in enumerate(("drift", "middle", "firm"))))
x2 = np.where(third == 2, df.FIRM_MULT, np.where(third == 0, df.DRIFT_MULT, 1.0))
print(f"\nlive stakes as they are: {u_st.sum():+.1f}u on {st.sum():.0f}u; with x{df.FIRM_MULT:g} firm third and x{df.DRIFT_MULT:g} drift third: {(u_st * x2).sum():+.1f}u on {(st * x2).sum():.0f}u")
