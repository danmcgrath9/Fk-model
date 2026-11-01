"""Write the day's export without the scratched runners, so every field-relative input is rebuilt on the real field.
python drop_scr.py IN_NPZ PRICES_TXT OUT_NPZ"""
import numpy as np, re, sys
inp, prices, out = sys.argv[1:4]
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
U=dict(np.load(inp)); scr=set(); listed=set()
for line in open(prices):
    pa=[x.strip() for x in line.split(",")]
    if len(pa)>=3 and pa[0].isdigit():
        listed.add((int(pa[0]),norm(pa[1])))
        if pa[2].upper()=="SCR": scr.add((int(pa[0]),norm(pa[1])))
rn=U["race_number"][U["race_idx"]]
# also drop runners the prices file does not list at all (1 Nov 2026: Cup Day R7 held 68 entries in Form King, stale
# nominations among the 24 accepted, and their missing ratings tripped the speed-rating STOP); only in races the
# prices file covers, and every name dropped this way is printed so a spelling mismatch cannot hide
races=sorted({r for r,_ in listed})
absent=np.array([int(r) in races and (int(r),norm(str(n))) not in listed for r,n in zip(rn,U["name"])])
if absent.any(): print("removing",absent.sum(),"runners not in the prices file:",[f"R{int(r)} {n}" for r,n in zip(rn[absent],U["name"][absent])])
keep=np.array([(int(r),norm(str(n))) not in scr for r,n in zip(rn,U["name"])]) & ~absent
print("removing",(~keep).sum(),"scratched runners:",[str(n) for n in U["name"][~keep]])
per_runner=[k for k,v in U.items() if hasattr(v,"shape") and v.shape[:1]==(len(keep),) and k not in ("cols","past_fields")]
for k in per_runner: U[k]=U[k][keep]
cnt=np.bincount(U["race_idx"],minlength=len(U["race_id"]))
U["field"]=cnt.astype(U["field"].dtype)
cols=list(U["cols"])
for c in ("numRunners","field_size","runners","starters"):
    if c in cols: U["X"][:,cols.index(c)]=cnt[U["race_idx"]]
np.savez(out,**U); print("fields now",dict(zip(U["race_number"].tolist(),cnt.tolist())))
