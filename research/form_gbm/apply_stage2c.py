"""apply second stage v3 (needs S in the day export) to a day's model json (p = the day's stage-1 blend). python apply_stage2c.py MODEL_JSON UP_NPZ OUT_JSON P_OOF"""
import numpy as np, bench as b, lightgbm as lgb, stage2, json, sys
model_json, up_npz, out_json, PF = sys.argv[1:5]
D=b.load(); p=np.load(PF); ri=D["race_idx"]
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
U=np.load(up_npz,allow_pickle=True); allrows=json.load(open(model_json)); uri=U["race_idx"]
key={(str(U["race_id"][uri[i]]),str(U["horse_id"][i])):i for i in range(len(uri))}
gone=[r for r in allrows if (r["race_id"],r["horse_id"]) not in key]; rows=[r for r in allrows if (r["race_id"],r["horse_id"]) in key]
print("not in export (kept at current price):",[r["horse"] for r in gone])
idx=np.array([key[(r["race_id"],r["horse_id"])] for r in rows])
up_p=np.array([r["p"] for r in rows]); up_ri=np.unique([r["race_id"] for r in rows],return_inverse=True)[1]; nRu=up_ri.max()+1
cat=lambda a,bb: np.concatenate([np.asarray(a).astype(str),np.asarray(bb).astype(str)])
hn=len(ri); rd=cat(D["date"][ri],U["date"][uri[idx]])
riall=np.concatenate([ri,up_ri+D["n_races"]]); pall=np.concatenate([p,up_p])
resall=np.concatenate([res,np.full(len(idx),np.nan)])
jc=list(U["cols"]).index("jockeyForm_lastTwelveMonthWinPercentage")
jw=np.concatenate([np.nan_to_num(D["X"][:,D["colidx"]["jockeyForm_lastTwelveMonthWinPercentage"]].astype(float),nan=0),np.nan_to_num(U["X"][idx,jc].astype(float),nan=0)])
pj=np.vstack([D["past_jockeys"].astype(str),U["past_jockeys"][idx].astype(str)]); lastj=np.array([next((x for x in row if x),"") for row in pj])
H_=cat(D["horse_id"],U["horse_id"][idx]); T_=cat(D["trainer"],U["trainer"][idx]); J_=cat(D["jockey"],U["jockey"][idx])
E=stage2.encodings(rd,H_,T_,J_,cat(D["sire"],U["sire"][idx]),cat(D["track"][ri],U["track"][uri[idx]]),resall)[hn:]
A,Bk,C=stage2.extras(rd,riall,H_,T_,J_,lastj,pall,jw,resall)
X,L=stage2.design(E,up_p,up_ri,nRu); SEC=stage2.sections(U["S"][idx],U["sec_fields"],U["P"][idx],U["past_fields"],up_ri,nRu); X=np.column_stack([X,A[hn:],Bk[hn:],C[hn:],SEC])
s=np.mean([lgb.Booster(model_file=f"stage2c_{k}.txt").predict(X) for k in range(3)],0)+L
e=np.exp(s-np.array([s[up_ri==r].max() for r in range(nRu)])[up_ri]); p2=e/np.bincount(up_ri,weights=e)[up_ri]
share={rid:sum(r["p"] for r in rows if r["race_id"]==rid) for rid in set(r["race_id"] for r in rows)}
for r,v in zip(rows,p2):
    r.setdefault("p_3way",r["p"]); r["p_stage1"]=r["p"]; r["p"]=float(v)*share[r["race_id"]]
for r in gone: r.setdefault("p_3way",r["p"])
json.dump(allrows,open(out_json,"w"),indent=1)
for r in sorted(rows,key=lambda r:-abs(np.log(r["p"]/r["p_stage1"])))[:8]: print(f"R{r['race']} {r['horse']:22s} ${1/r['p_stage1']:6.2f} -> ${1/r['p']:6.2f}")
