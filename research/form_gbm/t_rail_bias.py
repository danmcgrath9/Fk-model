"""Track x rail x run style (15 Oct 2026, founder: "a true rail at Caulfield plays leaderish, but a rail out 9m you want
to be midfield and getting wide"). Rails and actual settling positions from scripts/race_rails.py (recovered from
later past-run records). For each cell: winners against what BSP expected, and against what the OPENING price
expected (the price we bet at), by the style the horse actually raced (the bias itself) and by Form King's predicted
settling position (what is known before the race).
python3.13 t_rail_bias.py RACE_RAILS.tsv"""
import numpy as np, sys, collections, bench as b
D = b.load("ds/model_ds_new.npz"); ri = D["race_idx"]; nR = D["n_races"]
rid = D["race_id"].astype(str); hid = D["horse_id"].astype(str); trk = D["track"].astype(str)
rail, sett = {}, {}
for line in open(sys.argv[1]):
    p = line.rstrip("\n").split("\t")
    if p[0] == "R": rail[p[1]] = float(p[2])
    elif p[0] == "S":
        try: sett[(p[1], p[2])] = (float(p[3]), float(p[4]) if p[4] not in ("None", "") else np.nan)
        except ValueError: pass
rm = np.array([rail.get(x, np.nan) for x in rid])[ri]
fld = np.bincount(ri, minlength=nR)[ri].astype(float)
act = np.array([sett.get((rid[ri[i]], hid[i]), (np.nan, np.nan))[0] for i in range(len(ri))])
c = D["colidx"]; pred = D["X"][:, c["sm_predicted_position"]].astype(float)
def style(pos):
    sh = (pos - 1) / np.maximum(fld - 1, 1)
    return np.where(np.isnan(pos), "", np.where(pos <= 1, "1 lead", np.where(sh < 0.34, "2 on pace", np.where(sh < 0.67, "3 midfield", "4 back"))))
band = np.where(np.isnan(rm), "", np.where(rm <= 0, "true", np.where(rm <= 4, "out 1-4m", np.where(rm <= 8, "out 5-8m", "out 9m+"))))
q = D["q"]; mk = D["mkt"]; won = (D["finish"] == 1)
okr = (np.bincount(ri, weights=(q > 0) & (mk > 0), minlength=nR) == np.bincount(ri, minlength=nR)) & (np.bincount(ri, weights=won, minlength=nR) == 1)
m0 = okr[ri]
races_with_rail = len(set(ri[m0 & (band != "")])); print(f"races with a rail: {races_with_rail} of {okr.sum()}  (by band: {dict(collections.Counter(band[np.unique(ri[m0], return_index=True)[1]]))})")
print(f"runners with an actual settling position: {np.isfinite(act[m0]).mean():.0%}")
def table(tracks, sty, label):
    print(f"\n### {label}\n| track | rail | style | runners | races | won | BSP expected | won/BSP | open expected | won/open |\n|---|---|---|---|---|---|---|---|---|---|")
    for t in tracks:
        mt = m0 & (trk[ri] == t) if t != "ALL" else m0
        for bnd in ("true", "out 1-4m", "out 5-8m", "out 9m+"):
            for s in ("1 lead", "2 on pace", "3 midfield", "4 back"):
                m = mt & (band == bnd) & (sty == s)
                if m.sum() < 30: continue
                w, eq, eo = won[m].sum(), q[m].sum(), mk[m].sum()
                print(f"| {t} | {bnd} | {s[2:]} | {m.sum()} | {len(set(ri[m]))} | {w} | {eq:.1f} | {100*w/eq:.0f}% | {eo:.1f} | {100*w/eo:.0f}% |")
majors = [t for t, n in collections.Counter(trk[np.unique(ri[m0 & (band != '')])]).most_common() if n >= 60]
table(["ALL"] + majors, style(act), "By how the horse ACTUALLY raced (the bias itself)")
table(["ALL"] + majors, style(pred), "By Form King's PREDICTED settling position (known before the race)")
np.save("rail_m.npy", rm)
