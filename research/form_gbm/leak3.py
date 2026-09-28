import numpy as np, bench as b
D=b.load(); F=np.load("F2.npy"); names=open("F2_names.txt").read().split("\n")
ri=D['race_idx']; pre=D['pre_jump'][ri]; dt=D['date'][ri]; tr,te=b.split()
recent=(dt>="2026-08-15")&~pre
gap=[j for j,n in enumerate(names) if np.isnan(F[pre,j]).mean()-np.isnan(F[recent,j]).mean()>0.4]
# model features in r.x that are race-relative speed/sectional figures: live has them as 0 when the race has none
xz=[j for j,n in enumerate(names) if n in ("speed_rel","speed_best_rel","finish_speed_rel","last600_rel","to600_rel")]
print(len(gap),"gap columns;", [names[j] for j in xz])
# what share of live runners have the speed rel at exactly 0
for j in xz: print(names[j], "zero on live", np.mean(F[pre,j]==0).round(2), "zero back", np.mean(F[recent,j]==0).round(2))
import gbm
model,it=gbm.fit(F,tr,D['q'])
g=gbm.predict(model,F)
F2=F.copy(); mask=np.isin(ri,te)&~pre
blank=mask&(np.random.default_rng(0).random(len(ri))<0.81)
for j in gap: F2[blank,j]=np.nan
for j in xz: F2[np.isin(ri,te)&~pre,j]=np.where(blank[np.isin(ri,te)&~pre], 0.0, F2[np.isin(ri,te)&~pre,j])
g2=gbm.predict(model,F2)
bk=te[~D['pre_jump'][te]]
print(b.fmt("market, back-filled", b.score(D['mkt'],bk)))
print(b.fmt("GBM, back-filled as stored", b.score(g,bk)))
print(b.fmt("GBM, back-filled, speed blanked like live", b.score(g2,bk)))
