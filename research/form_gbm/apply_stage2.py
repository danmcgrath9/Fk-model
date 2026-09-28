import numpy as np, bench as b, lightgbm as lgb, stage2, json, sys
model_json, up_npz, out_json = sys.argv[1:4]
D=b.load(); p=np.load("p_oof.npy"); ri=D["race_idx"]
res=np.clip(np.log(np.maximum(D["q"],1e-4))-np.log(np.maximum(p,1e-4)),-3,3)
U=np.load(up_npz); rows=json.load(open(model_json))
uri=U["race_idx"]; key={(str(U["race_id"][uri[i]]),str(U["horse_id"][i])):i for i in range(len(uri))}
allrows=rows; gone=[r for r in rows if (r["race_id"],r["horse_id"]) not in key]; rows=[r for r in rows if (r["race_id"],r["horse_id"]) in key]
print("not in export (kept at current price):",[r["horse"] for r in gone])
idx=[key[(r["race_id"],r["horse_id"])] for r in rows]
print("matched",len(idx),"of",len(rows),"; upcoming runners",len(uri))
up_p=np.array([r["p"] for r in rows]); up_ri=np.unique([r["race_id"] for r in rows],return_inverse=True)[1]
cat=lambda a,bb: np.concatenate([np.asarray(a).astype(str),np.asarray(bb).astype(str)])
E=stage2.encodings(cat(D["date"][ri],U["date"][uri[idx]]),cat(D["horse_id"],U["horse_id"][idx]),cat(D["trainer"],U["trainer"][idx]),
                   cat(D["jockey"],U["jockey"][idx]),cat(D["sire"],U["sire"][idx]),cat(D["track"][ri],U["track"][uri[idx]]),
                   np.concatenate([res,np.full(len(idx),np.nan)]))[len(ri):]
nR=up_ri.max()+1; X,L=stage2.design(E,up_p,up_ri,nR)
s=np.mean([lgb.Booster(model_file=f"stage2_{k}.txt").predict(X) for k in range(3)],0)+L
e=np.exp(s-np.array([s[up_ri==r].max() for r in range(nR)])[up_ri]); p2=e/np.bincount(up_ri,weights=e)[up_ri]
print("runners with a horse history:",int((E[:,0]!=0).sum()),"of",len(idx))
share={rid:sum(r["p"] for r in rows if r["race_id"]==rid) for rid in set(r["race_id"] for r in rows)}
for r,v in zip(rows,p2): r["p_3way"]=r["p"]; r["p"]=float(v)*share[r["race_id"]]
for r in gone: r["p_3way"]=r["p"]
json.dump(allrows,open(out_json,"w"),indent=1)
moves=sorted(rows,key=lambda r:-abs(np.log(r["p"]/r["p_3way"])))[:10]
for r in moves: print(f"R{r['race']} {r['horse']:22s} ${1/r['p_3way']:6.2f} -> ${1/r['p']:6.2f}")
