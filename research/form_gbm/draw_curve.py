import json, math, os
S=os.environ["S"]
d=json.load(open("curve.json")); n=len(d["dates"])
W,H=900,420; L,Rm,T,B=70,120,30,44
series=[("open",d["cum_open"]),("ded",d["cum_ded"]),("bsp",d["cum_bsp"])]
ymin=min(min(v) for _,v in series); ymin=min(ymin,0); ymax=max(max(v) for _,v in series)
step=25000; y0=math.floor(ymin/step)*step; y1=math.ceil(ymax/step)*step
X=lambda i: L+(W-L-Rm)*i/(n-1); Y=lambda v: T+(H-T-B)*(y1-v)/(y1-y0)
col={"open":"var(--s1)","ded":"var(--s2)","bsp":"var(--s3)"}
g=[]
for v in range(int(y0),int(y1)+1,step): g.append(f"<line x1='{L}' x2='{W-Rm}' y1='{Y(v):.1f}' y2='{Y(v):.1f}' class='grid'/><text x='{L-8}' y='{Y(v)+4:.1f}' class='ax' text-anchor='end'>${v/1000:,.0f}k</text>")
seen={}
for i,dt in enumerate(d["dates"]):
    m=dt[:7]
    if m not in seen: seen[m]=i
names={"2026-05":"May","2026-06":"Jun","2026-07":"Jul","2026-08":"Aug","2026-09":"Sep","2026-10":"Oct"}
for m,i in seen.items(): g.append(f"<line x1='{X(i):.1f}' x2='{X(i):.1f}' y1='{T}' y2='{H-B}' class='grid'/><text x='{X(i)+4:.1f}' y='{H-B+16}' class='ax'>{names.get(m,m)}</text>")
g.append(f"<line x1='{L}' x2='{W-Rm}' y1='{Y(0):.1f}' y2='{Y(0):.1f}' class='zero'/>")
paths=[]; labels=[]
for k,vals in series:
    pts=" ".join(f"{X(i):.1f},{Y(v):.1f}" for i,v in enumerate(vals))
    paths.append(f"<polyline points='{pts}' fill='none' stroke='{col[k]}' stroke-width='2' stroke-linejoin='round'/>")
    labels.append([Y(vals[-1]),f"<text x='{W-Rm+8}' y='__Y__' class='lbl'><tspan fill='{col[k]}'>●</tspan> ${vals[-1]/1000:+,.0f}k</text>"])
labels.sort(key=lambda t:t[0]); last=None
for lb in labels:
    if last is not None and lb[0]<last+14: lb[0]=last+14
    last=lb[0]
labels=[t.replace("__Y__",f"{y+4:.1f}") for y,t in labels]
tt=json.dumps(dict(dates=d["dates"],open=d["cum_open"],ded=d["cum_ded"],bsp=d["cum_bsp"]))
svg=(f"<svg viewBox='0 0 {W} {H}' width='100%' role='img' aria-label='Cumulative profit of the live betting rules over 1,186 bets, May to October 2026, at the opening price, after an average deduction, and at Betfair SP' id='curve'>"
 "<style>.grid{stroke:var(--grid);stroke-width:1}.zero{stroke:var(--txt2);stroke-width:1}.ax{font:12px -apple-system,system-ui,sans-serif;fill:var(--txt2)}.lbl{font:600 13px -apple-system,system-ui,sans-serif;fill:var(--txt);font-variant-numeric:tabular-nums}</style>"
 +"".join(g)+"".join(paths)+"".join(labels)+
 f"<line id='xh' x1='0' x2='0' y1='{T}' y2='{H-B}' stroke='var(--txt2)' stroke-dasharray='3 3' visibility='hidden'/><rect x='{L}' y='{T}' width='{W-L-Rm}' height='{H-T-B}' fill='transparent' id='hit'/></svg><div id='tip' class='tip' hidden></div>")
mo=d["months"]; cls=lambda v: 'pos' if v>=0 else 'neg'
rows="".join(f"<tr><td>{names.get(m,m)} 2026</td><td>${v['inv']:,.0f}</td><td class='{cls(v['open'])}'>${v['open']:+,.0f}</td><td class='{cls(v['ded'])}'>${v['ded']:+,.0f}</td><td class='{cls(v['bsp'])}'>${v['bsp']:+,.0f}</td></tr>" for m,v in mo.items())
t=d["totals"]
js=("<script>const D=%s;const svg=document.getElementById('curve'),hit=document.getElementById('hit'),xh=document.getElementById('xh'),tip=document.getElementById('tip');const n=D.dates.length,L=%d,W=%d,Rm=%d;const f=v=>v.toLocaleString('en-AU',{style:'currency',currency:'AUD',maximumFractionDigits:0});"
    "hit.addEventListener('mousemove',e=>{const r=svg.getBoundingClientRect();const x=(e.clientX-r.left)*W/r.width;const i=Math.max(0,Math.min(n-1,Math.round((x-L)/(W-L-Rm)*(n-1))));const px=L+(W-L-Rm)*i/(n-1);xh.setAttribute('x1',px);xh.setAttribute('x2',px);xh.setAttribute('visibility','visible');tip.hidden=false;"
    "tip.innerHTML='<b>Bet '+(i+1)+' · '+D.dates[i]+'</b><br>Open '+f(D.open[i])+'<br>Less deductions '+f(D.ded[i])+'<br>BSP '+f(D.bsp[i]);tip.style.left=Math.min(e.clientX+12,window.innerWidth-200)+'px';tip.style.top=(e.clientY+12)+'px';});"
    "hit.addEventListener('mouseleave',()=>{xh.setAttribute('visibility','hidden');tip.hidden=true;});</script>") % (tt,L,W,Rm)
block=(f"<h2>The curve</h2><div class='sub'>Cumulative profit over the 1,186 bets in date order, $100 a unit, final staking plan. Three lines: the opening price as recorded, the same less the live book's average deduction for late scratchings (17.8c in the dollar per race across 26 races, 13 of them with a deduction), and Betfair SP.</div>"
 f"<div class='legend'><span><i style='background:var(--s1)'></i>At the opening price <b>${t['open']:+,.0f}</b></span><span><i style='background:var(--s2)'></i>Open less average deductions <b>${t['ded']:+,.0f}</b></span><span><i style='background:var(--s3)'></i>At Betfair SP <b>${t['bsp']:+,.0f}</b></span></div>"
 f"<div class='chart'>{svg}</div><details><summary>Month by month (table)</summary><table><tr><th>Month</th><th>Invested</th><th>Open</th><th>Open less deductions</th><th>BSP</th></tr>{rows}</table></details>{js}")
css="<style>:root{--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--grid:#e6e5e2;--txt:#0b0b0b;--txt2:#52514e}@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--s1:#3987e5;--s2:#d95926;--s3:#199e70;--grid:#383835;--txt:#fff;--txt2:#c3c2b7}}:root[data-theme=dark]{--s1:#3987e5;--s2:#d95926;--s3:#199e70;--grid:#383835;--txt:#fff;--txt2:#c3c2b7}.chart{margin:8px 0 10px}.legend{display:flex;flex-wrap:wrap;gap:10px 22px;font-size:13.5px;margin:10px 0}.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}.legend b{font-variant-numeric:tabular-nums;margin-left:4px}.tip{position:fixed;background:var(--txt);color:#fff;font:12.5px/1.4 -apple-system,system-ui,sans-serif;padding:6px 9px;border-radius:5px;pointer-events:none;font-variant-numeric:tabular-nums;z-index:9}details{margin:6px 0 16px}summary{cursor:pointer;font-size:14px;color:var(--txt2)}</style>"
p=f"{S}/pages/backtest-v5.html"; s=open(p).read()
assert "<div class='box'><b>Read this first.</b>" in s
s=s.replace("<div class='box'><b>Read this first.</b>",css+block+"<div class='box'><b>Read this first.</b>",1)
s=s.replace("Deductions for late scratchings are not in these figures (in the live paper book they have cost about a third of the gross).","The tables below carry no deductions for late scratchings; the orange line in the chart applies the live book's average (17.8c in the dollar per race), which takes the open figure from +64.7% to about +35%.")
open(p,"w").write(s); print("ok")
