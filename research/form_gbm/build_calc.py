import json, re, sys, html
L="/home/user/fk-model/data/live_bets/"
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
def data(model,prices,sb=(),ang=None,fs=(),fu=None):
    ang=ang or {}; fu=fu or {}; fuk={(int(k.split('|')[0]),norm(k.split('|',1)[1])):v for k,v in fu.items()}; fsk={(int(k.split('|')[0]),norm(k.split('|',1)[1])) for k in fs}
    sbk={(int(r),norm(h)) for r,h in sb}
    rows=json.load(open(L+model)); pr={}; scr=set()
    for line in open(L+prices):
        pa=[x.strip() for x in line.split(",")]
        if len(pa)>=3 and pa[0].isdigit():
            k=(int(pa[0]),norm(pa[1]))
            if pa[2].upper()=="SCR": scr.add(k); continue
            o=float(pa[2]); n=float(pa[3]) if len(pa)>=4 and pa[3] else o; pr[k]=(o,n)
    races={}
    for r in rows:
        k=(r["race"],norm(r["horse"]))
        races.setdefault(r["race"],[]).append(dict(h=r["horse"],b=r["barrier"],j=r["jockey"],p=round(r["p"],6),s=bool(r["solid"]),
            o=pr.get(k,(None,None))[0],n=pr.get(k,(None,None))[1],x=k in scr,sb=k in sbk,fs=k in fsk,fu=fuk.get(k,""),a=ang.get(f"{r['race']}|{r['horse']}",[])))
    for v in races.values(): v.sort(key=lambda r:-r["p"])
    return races
if __name__=="__main__":
  TPL=open("calc_tpl.html").read()
  title,model,prices,out,key,sub=sys.argv[1:7]
  open(out,"w").write(TPL.replace("__TITLE__",html.escape(title)).replace("__SUB__",html.escape(sub)).replace("__KEY__",key).replace("__DATA__",json.dumps(data(model,prices))))
  print("ok",out)
