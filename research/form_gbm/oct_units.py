import re,json,sys
S=sys.argv[1]
res={}; cur=None
for l in open(S+'/res_all.txt'):
    if l.startswith('## '): cur=int(l.split(':')[0][-2:]); continue
    m=re.match(r"R(\d+) (.+?)\s+finish (\S+)\s+SP (\S+)\s+BSP (\S+)",l)
    if m: res.setdefault((cur,m.group(2).strip().lower()),(m.group(3),m.group(4),m.group(5)))
B=[]
rows=open('data/live_bets/forward-test-betmatic.md').read().split('## Every fill')[1].splitlines()
for l in rows:
    c=[x.strip() for x in l.split('|')]
    if len(c)<13 or 'Oct' not in c[1]: continue
    d=int(re.match(r'\w+ (\d+) Oct',c[1]).group(1))
    if d>16: continue
    s=float(c[8].rstrip('u')); o=float(c[6].strip('$')); ded=float(c[11].rstrip('c'))/100 if c[11] else 0
    B.append(dict(d=d,h=c[3],u=s,p=round(1+(o-1)*(1-ded),2),src='ft',ledger_pl=float(c[12])))
def card(f,d):
    j=json.load(open('branding/mercer-tipping/'+f))
    for m in j['meetings']:
        for b in m['bets']:
            pr=str(b.get('price','')); un=str(b.get('units',''))
            if 'SCR' in pr.upper() or 'REF' in pr.upper() or 'SCR' in un.upper(): continue
            p=float(pr.strip('$')) if re.match(r'^\$[\d.]+$',pr) else None
            B.append(dict(d=d,h=b['horse'],u=float(un.rstrip('u')),p=p,src=f))
for f,d in [('card_sat17_open_caulfield.json',17),('card_sat17_open_country.json',17),('card_sun18_open.json',18),('card_mon19_plain.json',19),('card_tue20_plain.json',20),('card_sat24.json',24),('card_mon26.json',26)]: card(f,d)
B+= [dict(d=21,h='Murshidi',u=5,p=11,src='book'),dict(d=22,h='Cresta Crystal',u=1.35,p=13.64,src='book'),dict(d=22,h='Grinding Away',u=1.44,p=21,src='book'),dict(d=22,h='Russian Benefits',u=2.5,p=14,src='book'),
     dict(d=23,h='Eye For An Eye',u=0.95,p=22.12,src='book'),dict(d=23,h='Superstock',u=1.24,p=14.44,src='book'),dict(d=25,h='Rough Enuff',u=1.12,p=6.34,src='book')]
miss=[]
for b in B:
    r=res.get((b['d'],b['h'].lower()))
    if not r: miss.append((b['d'],b['h'],b['src'])); continue
    b['fin']=r[0]; b['sp']=None if r[1]=='None' else float(r[1]); b['bsp']=None if r[2]=='None' else float(r[2])
    if b['p'] is None: b['p']=b['sp']
print('missing',miss)
for b in B:
    if b.get('fin')=='None': print('no finish (scratched?)',b['d'],b['h'],b['src'])
json.dump(B,open(S+'/oct_units.json','w'),indent=0)
print(len(B))
