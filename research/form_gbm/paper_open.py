"""Paper bets struck at the opening price for a priced meeting. python paper_open.py MODEL_JSON PRICES_TXT ANG_JSON OUT_CSV [HURDLE_RACES] [FS_JSON] [FU_JSON]

First-starter rule (4 Oct 2026, t_fs_split.py): no EDGE or value bet on a first-starter (FS_JSON from fs_json.py), and none in a
race with a first-starter at $6 or shorter at the open. Like the race page, no value bet when our price is $50+ or the
open is 3x our price or more. Stake (4 Oct 2026, t_stakeplan.py): EDGE and value bets take Kelly x75 on a 50/50 blend of our chance and the market's,
capped at 4 units (average about 2 units); top pick 1 unit.
Top pick is a tracking plan and stays unless the top pick is a first-starter."""
import json, re, csv, collections, sys
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
mj,pt,aj,out=sys.argv[1:5]; hurdle={int(x) for x in sys.argv[5].split(",")} if len(sys.argv)>5 and sys.argv[5] else set()
fs=set(json.load(open(sys.argv[6]))) if len(sys.argv)>6 and sys.argv[6] else set()
_fu=json.load(open(sys.argv[7])) if len(sys.argv)>7 and sys.argv[7] else {}
fu={k.split('|')[0]+'|'+norm(k.split('|',1)[1]) for k,v in _fu.items() if not v.startswith("EARLY:")}
early={k.split('|')[0]+'|'+norm(k.split('|',1)[1]) for k,v in _fu.items() if v.startswith("EARLY:")}   # allowed at $8 or shorter at the open; tagged early_only
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
    isfs=lambda r: f"{k}|{r['horse']}" in fs
    fs_backed=any(isfs(r) and (k,norm(r["horse"])) in pr and pr[(k,norm(r["horse"]))][0]<=6 for r in rs)
    for r in rs:
        key=(k,norm(r["horse"]))
        if key not in pr: continue
        op,cur=pr[key]; pp=r["p"]/tot; val=pp*op-1; a=ang.get(f"{k}|{r['horse']}",[])
        # same caps as the race page (market_tpl.html): our price under $50 and the open under 3x our price
        hk=f"{k}|{norm(r['horse'])}"; is_early=hk in early
        bet_ok=not isfs(r) and not fs_backed and hk not in fu and 1/pp<50 and op<3/pp and not (is_early and op>8)
        tags=(["EDGE"] if bet_ok and val>=0.2 and a else [])+(["value_20c"] if bet_ok and val>=0.2 else [])+(["top_pick"] if r is top and not isfs(r) else [])
        for t in tags:
            rows.append(dict(race=k,race_id=r["race_id"],horse=r["horse"],plan=t,price=op,price_now=cur,model_price=round(1/pp,2),value=round(val,3),
                             angles="; ".join(a)+("; EARLY ONLY: bet near the open" if is_early else ""),stake=(round(min(4.0,75*max(0.0,((pp/op)**0.5*op-1)/(op-1))),2) if t in ("EDGE","value_20c") else 1.0),hurdle="yes" if k in hurdle else "no",result="",returned=""))
with open(out,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows:
    if r["plan"]=="EDGE": print(f"R{r['race']} {r['horse']:20s} open ${r['price']:6.2f} ours ${r['model_price']:6.2f} value +{round(100*r['value'])}%")
print(dict(collections.Counter(r["plan"] for r in rows)))
