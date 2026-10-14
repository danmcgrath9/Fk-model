"""Backtest vs forward test on the same races (5-9 Oct 2026), founder 14 Oct: "we can just up the stake".
Why does live stake ~0.45u a race when the backtest stakes ~1.6u? Same races, swap the inputs one at a time:
the model's price (backtest p2 vs the v6 file actually made before the race) and the opening price (backtest
'open' vs the Form King snapshot the forward test filled at)."""
import numpy as np, json, re, subprocess, sys, collections
exec(open('t_m3.py').read().split('import sys')[0])
sys.path.insert(0, '/home/user/fk-model/research/form_gbm'); from opens import parse_opens
REPO='/home/user/fk-model'; L=REPO+'/data/live_bets'
norm_=lambda s: re.sub(r'[^a-z0-9]','',str(s).lower())
def git_first(path):
    h=subprocess.run(['git','-C',REPO,'log','--diff-filter=A','--format=%h','--',path],capture_output=True,text=True).stdout.split()
    r=subprocess.run(['git','-C',REPO,'show',f'{h[-1]}:{path}'],capture_output=True,text=True); return json.loads(r.stdout)
M=[('2026-10-05','Pakenham Synthetic','2026-10-05-pakenham','','2026-10-05-pakenham-prices.txt'),
   ('2026-10-06','Mildura','2026-10-06-mildura','g4','2026-10-06-mildura-prices-monday.txt'),
   ('2026-10-07','Geelong','2026-10-07-geelong','s6','2026-10-07-geelong-prices-monday.txt'),
   ('2026-10-08','Kyneton','2026-10-08-kyneton','g4','2026-10-08-kyneton-prices-wed.txt'),
   ('2026-10-09','Ballarat','2026-10-09-ballarat','g4','2026-10-09-ballarat-prices.txt'),
   ('2026-10-09','Cranbourne','2026-10-09-cranbourne','g4','2026-10-09-cranbourne-prices-thu930.txt')]
pm_b,_=samples['HOLD']; name=np.asarray(D['name']).astype(str); rn=np.array([int(str(x).split('_')[-1]) for x in np.asarray(D['race_id'])])[ri]
o_b=o.copy(); pm_live=np.full(len(ri),np.nan); o_live=np.full(len(ri),np.nan); sel=np.zeros(len(ri),bool)
for d,tk,pre,g,snap in M:
    B=f'{pre}-{g}' if g else pre; v=git_first(f'data/live_bets/{B}-v6.json')
    lp={(int(r['race']),norm_(r['horse'])):r.get('p_model',r['p']) for r in v}
    op={}
    for l in open(f'{L}/{snap}'):
        pa=[x.strip() for x in l.split('#')[0].split(',')]
        if len(pa)>=3 and pa[0].isdigit() and not pa[2].upper().startswith('SCR'):
            fk,tab=parse_opens(', '.join(pa[3:])); op[(int(pa[0]),norm_(pa[1]))]=fk or tab
    m=(dates==d)&(track==tk); sel|=m
    for i in np.where(m)[0]:
        k=(rn[i],norm_(name[i])); pm_live[i]=lp.get(k,np.nan); o_live[i]=op.get(k,np.nan)
ins=sel
races=len(np.unique(ri[ins&race_ok[ri]&np.isfinite(bs)]))
both=sel&np.isfinite(pm_live)&np.isfinite(o_live)&okp
print(f'{sel.sum()} runners in {races} races; matched to the live files: {both.sum()}')
r1=np.median(o_b[both]/o_live[both]); print(f'opening price, backtest / Form King snapshot: median {r1:.3f}; backtest higher on {(o_b[both]>o_live[both]).mean():.0%}, lower on {(o_b[both]<o_live[both]).mean():.0%}')
bk_b=np.bincount(ri[both],weights=1/o_b[both],minlength=nR); bk_l=np.bincount(ri[both],weights=1/o_live[both],minlength=nR); rr=np.unique(ri[both])
print(f'opening book: backtest median {np.median(bk_b[rr]):.3f}, Form King snapshot median {np.median(bk_l[rr]):.3f}')
print(f'model probability, backtest p2 / live v6: median {np.median(pm_b[both]/pm_live[both]):.3f}')
def summ(lbl,pm,oo):
    global o
    o=np.where(both,oo,np.nan) if oo is not None else o_b
    pmx=np.where(both,pm,0.0); out=run(pmx,ins&both,1.2); o=o_b.copy()
    st=sum(x[1] for x in out); pl=sum(x[2] for x in out)
    print(f'| {lbl} | {len(out)} | {st:.2f}u | {st/races:.2f}u | {pl:+.2f}u |')
print(f'\n| model price / opening price | bets | staked | per race | profit (16c ded.) |\n|---|---|---|---|---|')
summ('backtest model / backtest open (the backtest)',pm_b,o_b)
summ('live model / backtest open',pm_live,o_b)
summ('backtest model / Form King open',pm_b,o_live)
summ('live model / Form King open (the forward test, no live rules)',pm_live,o_live)
print('\nforward test actual on these 6 meetings (live rules on): 23 bets, 24.82u')

# why the live model is less confident: field size and probability totals per race
print('\n| meeting | races | runners in backtest | runners in the live file | live p total of backtest runners | backtest p2 total |\n|---|---|---|---|---|---|')
for d,tk,pre,g,snap in M:
    B=f'{pre}-{g}' if g else pre; v=git_first(f'data/live_bets/{B}-v6.json')
    m=(dates==d)&(track==tk); rr=np.unique(ri[m])
    lp=collections.defaultdict(float); ln=collections.Counter()
    for r in v: ln[int(r['race'])]+=1
    print(f"| {tk} | {len(rr)} | {m.sum()/len(rr):.1f} | {sum(ln.values())/len(ln):.1f} | {np.nansum(pm_live[m])/len(rr):.3f} | {pm_b[m].sum()/len(rr):.3f} |")
# live rules on these races, from the live files
fsn=set(); fu={}
for d,tk,pre,g,snap in M:
    B=f'{pre}-{g}' if g else pre
    fsv=json.load(open(f'{L}/{B}-first-starters.json')); fuv=json.load(open(f'{L}/{B}-first-up-blocks.json'))
    for k in fsv: fsn.add((d,tk,int(k.split('|')[0]),norm_(k.split('|',1)[1])))
    for k,vv in fuv.items(): fu[(d,tk,int(k.split('|')[0]),norm_(k.split('|',1)[1]))]=vv
key=lambda i:(dates[i],track[i],rn[i],norm_(name[i]))
o=o_live.copy(); pmx=np.where(both,pm_live,0.0); out=run(pmx,ins&both,1.2); o=o_b.copy()
isfs=np.array([key(i) in fsn for i in range(len(ri))])
fs_short=np.zeros(nR,bool)
for i in np.where(isfs&np.isfinite(o_live)&(o_live<=6))[0]: fs_short[ri[i]]=True
stages=collections.OrderedDict([('first starter',lambda i: isfs[i]),('first-starter race rule',lambda i: fs_short[ri[i]]),
  ('first-up/bounce block',lambda i: bool(fu.get(key(i),'')) and not fu.get(key(i),'').startswith('EARLY')),
  ('EARLY over $8',lambda i: fu.get(key(i),'').startswith('EARLY') and o_live[i]>8)])
left=list(out); print(f'\nlive model, Form King open, no rules: {len(left)} bets, {sum(x[1] for x in left):.2f}u, {sum(x[2] for x in left):+.2f}u')
for lbl,f in stages.items():
    cut=[x for x in left if f(x[0])]; left=[x for x in left if not f(x[0])]
    print(f'- {lbl}: removes {len(cut)} bets, {sum(x[1] for x in cut):.2f}u (their profit {sum(x[2] for x in cut):+.2f}u) -> {len(left)} bets, {sum(x[1] for x in left):.2f}u')
# the live model re-spread over the horses that actually ran (what pricing on the final field does)
s=np.bincount(ri,weights=np.where(both,pm_live,0),minlength=nR); pm_rn=np.where(both,pm_live/np.where(s[ri]>0,s[ri],1),0)
o=o_live.copy(); out=run(pm_rn,ins&both,1.2); o=o_b.copy()
print(f'\nlive model re-spread over the runners that ran, Form King open, no rules: {len(out)} bets, {sum(x[1] for x in out):.2f}u ({sum(x[1] for x in out)/races:.2f}u a race), {sum(x[2] for x in out):+.2f}u')
left=list(out)
for lbl,f in stages.items(): left=[x for x in left if not f(x[0])]
print(f'same with every live rule: {len(left)} bets, {sum(x[1] for x in left):.2f}u ({sum(x[1] for x in left)/races:.2f}u a race), {sum(x[2] for x in left):+.2f}u')
