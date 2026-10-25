"""Public-overreaction hypotheses at BSP (25 Oct 2026, founder: "there would have to be betting angles"). No model:
each is a thing punters are said to overbet or underbet, scored at BSP on the clean holdout (races from 3 Jun 2026 with
an open and a BSP on every runner), both date halves; A/E = wins / BSP's expectation; lay and back at BSP, 8% comm.
python3.13 t_bsp_public.py"""
import numpy as np
exec(open("t_bsp_angles.py").read().split("# A. back at the open")[0])
X = z["X"]; cols = list(z["cols"]); col = lambda n: X[:, cols.index(n)].astype(float)
P = z["P"].astype(float); pf = list(z["past_fields"]); last_fin = P[:, 0, pf.index("finish")]
fs = col("first_starter") == 1; jw = col("jockey_win"); bar = col("barrier"); fld = z["field"].astype(float)[ri]
gear = col("gear_first_time") == 1; days = col("daysSinceLastRace"); app = col("apprenticeJockey") == 1
# favourite = lowest BSP in the race
favb = np.full(nR, np.inf); np.minimum.at(favb, ri, np.where(m, bs, np.inf)); fav = m & (bs == favb[ri])
drift = qo / qb
jcut = np.nanquantile(jw[m], 2 / 3); topj = jw >= jcut
H = "| angle | early: runners / wins / A/E / lay ROI / back ROI | late: same |\n|---|---|---|"
def band(name, g):
    print(f"\n## {name}\n" + H)
    for lo_, hi_ in ((1, 2.5), (2.5, 4), (4, 8), (8, 15), (15, 30), (30, 1000)): row(f"${lo_}-${hi_}", g & (bs >= lo_) & (bs < hi_))
    row("all", g)
band("1. First starters", m & fs)
band("2. Last-start winners", m & (last_fin == 1))
band("3. Last-start winners that firmed 25%+ from the open (public double-up)", m & (last_fin == 1) & (drift < 0.8))
band("4. Last-start winners that drifted 25%+", m & (last_fin == 1) & (drift >= 1.25))
print("\n## 5. Favourites by field size\n" + H)
for lo_, hi_ in ((2, 8), (9, 12), (13, 30)): row(f"field {lo_}-{hi_}", fav & (fld >= lo_) & (fld <= hi_))
row("fav under $2.5, field 13+", fav & (bs < 2.5) & (fld >= 13)); row("fav $2.5-$4, field 13+", fav & (bs >= 2.5) & (bs < 4) & (fld >= 13))
band("6. Top-third jockeys (12-month win rate)", m & topj)
band("7. First-time gear", m & gear)
band("8. First-up (84+ days)", m & (days >= 84) & ~fs)
band("9. Apprentice-ridden", m & app)
print("\n## 10. Barriers in fields of 12+\n" + H)
row("barrier 1-3", m & (fld >= 12) & (bar <= 3)); row("barrier 4-8", m & (fld >= 12) & (bar >= 4) & (bar <= 8)); row("barrier 9+", m & (fld >= 12) & (bar >= 9))
band("11. Beaten favourite last start (last-start fav, finished 2nd-4th)", m & (P[:, 0, pf.index("sp")] <= 3.0) & (last_fin >= 2) & (last_fin <= 4))
