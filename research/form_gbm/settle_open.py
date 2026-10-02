"""Settle open-price paper bets from a reports-branch page. python settle_open.py BETS_CSV REPORT_HTML DEDUCTIONS_CSV [FS_RACES]"""
import csv, re, html, sys, collections
norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
bets_p,rep_p,ded_p=sys.argv[1:4]
s=open(rep_p).read(); res={}
for rn in range(1,13):
    i=s.find(f"id='race-{rn}'")
    if i<0: continue
    j=s.find("id='race-",i+10); seg=s[i:j if j>0 else None]
    rows=[[html.unescape(re.sub(r"<[^>]+>","",x)).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>",tr,re.S)] for tr in re.findall(r"<tr[^>]*>(.*?)</tr>",seg,re.S)]
    if not rows or "Result" not in rows[0]: continue
    k=rows[0].index("Result")
    for r in rows[1:]:
        if r and r[0]=="Runner": break          # the next table on the page; only the first carries results
        if len(r)>k: res[(rn,norm(r[0]))]=r[k]
ded={int(r["race"]):float(r["deduction"]) for r in csv.DictReader(open(ded_p))}
rows=list(csv.DictReader(open(bets_p))); fields=list(rows[0])
for f in ["result","returned","deduction","effective_price","profit","profit_no_deduction"]:
    if f not in fields: fields.append(f)
miss=[]
for r in rows:
    rn=int(r["race"]); t=res.get((rn,norm(r["horse"])),"")
    if not t: miss.append(f"R{rn} {r['horse']}"); t="SCR (refund)"
    if t.startswith("SCR"):
        r.update(result=t,deduction="0.000",effective_price=r["price"],returned=r["stake"],profit="0.00",profit_no_deduction="0.00"); continue
    won=t.startswith("1st"); d=ded.get(rn,0.0); op=float(r["price"]); st=float(r["stake"])
    eff=op*(1-d)
    r.update(result=t,deduction=f"{d:.3f}",effective_price=f"{eff:.2f}",returned=f"{st*eff:.2f}" if won else "0.00",
             profit=f"{st*eff-st if won else -st:.2f}",profit_no_deduction=f"{st*op-st if won else -st:.2f}")
w=csv.DictWriter(open(bets_p,"w",newline=""),fieldnames=fields); w.writeheader(); w.writerows(rows)
print("missing results:",miss)
