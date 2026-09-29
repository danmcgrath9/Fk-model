import numpy as np, json, re, pandas as pd
H=np.load("ds/model_ds.npz"); U=np.load("up/upcoming.npz"); f={n:i for i,n in enumerate(H["past_fields"])}
frames=[]
for Z in (H,U):
    P=Z["P"].astype(float); pid=Z["past_race_ids"].astype(str); tr=P[:,:,f["trial"]]==1; t6=P[:,:,f["to600"]]
    hid=np.repeat(Z["horse_id"].astype(str)[:,None],10,1)
    m=(~tr)&np.isfinite(t6)&(pid!="")
    frames.append(pd.DataFrame({"pid":pid[m],"h":hid[m],"t":t6[m]}))
df=pd.concat(frames).drop_duplicates(["pid","h"]); g=df.groupby("pid")["t"].agg(["mean","count"])
T=np.load("late_feats.npy"); q5=np.nanquantile(T[:,1][np.isfinite(T[:,1])],0.8)
P=U["P"].astype(float); pid=U["past_race_ids"].astype(str); tr=P[:,:,f["trial"]]==1
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
M={(r["race"],norm(r["horse"])):r for r in json.load(open("/home/user/fk-model/data/live_bets/2026-09-30-ballarat-model5.json"))}
pr={}; scr=set()
for line in open("/home/user/fk-model/data/live_bets/2026-09-30-ballarat-prices-fk.txt"):
    pa=[x.strip() for x in line.split(",")]
    if len(pa)>=3 and pa[0].isdigit():
        k=(int(pa[0]),norm(pa[1]))
        if pa[2].upper()=="SCR": scr.add(k)
        else: pr[k]=float(pa[3]) if len(pa)>=4 and pa[3] else float(pa[2])
tot={}
for (r,h),m in M.items():
    if (r,h) not in scr: tot[r]=tot.get(r,0)+m["p"]
rn=U["race_number"][U["race_idx"]]
SB=[]
print(f"threshold: {q5:.2f}L beyond tempo, rated at or below class")
for i in range(len(U["horse_id"])):
    ok=~tr[i]&np.isfinite(P[i,:,f["last600"]])
    if not ok.any(): continue
    j=int(np.argmax(ok))
    if pid[i,j] not in g.index or g.loc[pid[i,j],"count"]<3: continue
    tempo=g.loc[pid[i,j],"mean"]; l6=P[i,j,f["last600"]]; lres=l6-(-3.94-0.35*tempo); vs=P[i,j,f["vsClass"]]
    k=(int(rn[i]),norm(str(U["name"][i])))
    if lres>=q5 and vs<=0 and k not in scr:
        SB.append([k[0],str(U["name"][i])])
        pp=M[k]["p"]/tot[k[0]]; now=pr.get(k); ev=pp*now-1
        flag="  << VALUE + SPRINGBOARD" if ev>0.2 and 1/pp<50 and now<3/pp else ""
        print(f"R{k[0]} {str(U['name'][i]):20s} last 600 {l6:+.2f}L, tempo {tempo:+.1f}L, {lres:+.2f}L beyond tempo, rated {vs:+.1f}L vs class | ours ${1/pp:.2f}, now ${now:.2f}, value {ev:+.0%}{flag}")

json.dump(SB,open("/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad/sb_ballarat.json","w"))
