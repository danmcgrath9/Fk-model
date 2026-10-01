"""Paper bets struck at the opening price for a priced meeting. python paper_open.py MODEL_JSON PRICES_TXT ANG_JSON OUT_CSV [HURDLE_RACES]"""
import json, re, csv, collections, sys
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
mj,pt,aj,out=sys.argv[1:5]; hurdle={int(x) for x in sys.argv[5].split(",")} if len(sys.argv)>5 and sys.argv[5] else set()
M=json.load(open(mj)); ang=json.load(open(aj)); pr={}; scr=set()
for l in open(pt):
    pa=[x.strip() for x in l.split(",")]
    if len(pa)>=3 and pa[0].isdigit():
        k=(int(pa[0]),norm(pa[1]))
        if pa[2].upper()=="SCR": scr.add(k)
        else: pr[k]=(float(pa[2]),float(pa[3]) if len(pa)>3 and pa[3] else float(pa[2]))
by=collections.defaultdict(list)
for r in M:
    if (r["race"],norm(r["horse"])) not in scr: by[r["race"]].append(r)
rows=[]
for k in sorted(by):
    rs=by[k]; tot=sum(r["p"] for r in rs); top=max(rs,key=lambda r:r["p"])
    for r in rs:
        key=(k,norm(r["horse"]))
        if key not in pr: continue
        op,cur=pr[key]; pp=r["p"]/tot; val=pp*op-1; a=ang.get(f"{k}|{r['horse']}",[])
        tags=(["EDGE"] if val>=0.2 and a else [])+(["value_20c"] if val>=0.2 else [])+(["top_pick"] if r is top else [])
        for t in tags:
            rows.append(dict(race=k,race_id=r["race_id"],horse=r["horse"],plan=t,price=op,price_now=cur,model_price=round(1/pp,2),value=round(val,3),
                             angles="; ".join(a),stake=1.0,hurdle="yes" if k in hurdle else "no",result="",returned=""))
with open(out,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows:
    if r["plan"]=="EDGE": print(f"R{r['race']} {r['horse']:20s} open ${r['price']:6.2f} ours ${r['model_price']:6.2f} value +{round(100*r['value'])}%")
print(dict(collections.Counter(r["plan"] for r in rows)))
