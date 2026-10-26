"""Mercer Tipping clean set (26 Oct 2026, founder: "start again and go clean ... how profitable we are, beating BSP but
also we tip at a profit at BSP"): $100 on every tip, three cards. 1 the money at our price and at Betfair SP; 2 the running
profit, both lines; 3 beating the market (tipped bigger than BSP, winners against what BSP expected). 1080x1350.
python cleancards.py PROFIT.json OUTDIR     PROFIT.json: profit_oct_to26.json ({"bets": [{"horse","date","taken","bsp","won"}]})"""
import asyncio, glob, json, statistics, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.k{{font:600 30px/1 BC;color:{PALE};letter-spacing:6px;text-transform:uppercase}}
.hero{{font:800 92px/0.95 BC;text-transform:uppercase;margin:46px 0 0}} .hero span{{color:{GOLD}}}
.money{{margin-top:60px;display:flex;flex-direction:column;gap:44px}}
.m .v{{font:800 190px/0.9 BC;font-variant-numeric:tabular-nums;letter-spacing:-2px}} .m .l{{font:600 34px/1 BC;color:{PALE};letter-spacing:4px;text-transform:uppercase;margin-top:12px}}
.g{{color:{GOLD}}} .w{{color:{INK}}}
.sub{{font:600 34px/1.3 BC;color:{PALE};margin-top:70px}} .sub b{{color:{INK}}}
svg text{{font-family:BC}} svg{{display:block}}
.stat{{display:grid;grid-template-columns:1fr;gap:10px;margin-top:54px}}
.stat .big{{font:800 150px/0.9 BC;color:{GOLD};font-variant-numeric:tabular-nums}} .stat .lab{{font:800 40px/1.1 BC;text-transform:uppercase}}
.track{{height:46px;border-radius:23px;background:{LINE};position:relative;overflow:hidden;margin-top:18px}}
.track i{{position:absolute;left:0;top:0;bottom:0;background:{GOLD};border-radius:23px}}
.track u{{position:absolute;top:-8px;bottom:-8px;width:6px;background:{INK};text-decoration:none}}
.cap{{display:flex;justify-content:space-between;font:600 28px/1 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:14px}}
"""
TOP = (f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
       "<div class='when'>October<span>{sub}</span></div></div>")
FOOT = "<div class='foot'><span>Win bets.</span><span>18+ · Gamble responsibly</span></div>"
def page(sub, body): return f"<html><head><style>{CSS}</style></head><body>{TOP.format(sub=sub)}{body}<div style='flex:1'></div>{FOOT}</body></html>"
def run(b, key, c=0.0):
    out = [0.0]
    for x in b: c += 100 * ((x[key] - 1) if x["won"] else -1); out.append(c)
    return out
def money(v): return f"{'+' if v >= 0 else '-'}${abs(v):,.0f}"
def card1(b):
    a, s = run(b, "taken")[-1], run(b, "bsp")[-1]; n = 100 * len(b)
    body = (f"<div class='hero'>$100 on <span>every tip</span></div>"
            f"<div class='money'><div class='m'><div class='v g'>{money(a)}</div><div class='l'>At the price we tipped · {100*a/n/100:+.0%}</div></div>"
            f"<div class='m'><div class='v w'>{money(s)}</div><div class='l'>At Betfair SP · {100*s/n/100:+.0%}</div></div></div>"
            f"<div class='sub'><b>{len(b)} tips</b>, 5 to 26 October. Miss our price and it still pays.</div>")
    return page("$100 a tip", body)
def chart(b, W=936, H=700):
    a, s = run(b, "taken"), run(b, "bsp"); n = len(b)
    hi, lo, step = 14000, -2000, 2000; L, R, T, B = 110, 150, 20, 50
    x = lambda i: L + i * (W - L - R) / n; y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    g = []
    v = lo
    while v <= hi:
        g.append(f"<line x1='{L}' x2='{W-R}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='{INK if v == 0 else LINE}' stroke-width='{3 if v == 0 else 2}'/>"
                 f"<text x='{L-16}' y='{y(v)+9:.1f}' text-anchor='end' font-size='26' font-weight='600' fill='{PALE}'>{'$0' if v == 0 else money(v)[:-4] + 'k' if abs(v) >= 1000 else money(v)}</text>")
        v += step
    for t in (5, 12, 19, 26):
        i = next((i for i, z in enumerate(b) if z["date"] >= t), None)
        if i is not None: g.append(f"<text x='{x(i):.1f}' y='{H-12}' text-anchor='middle' font-size='26' font-weight='600' fill='{PALE}'>{b[i]['date']} Oct</text>")
    pl = lambda r, c, w: f"<polyline fill='none' stroke='{c}' stroke-width='{w}' stroke-linejoin='round' points='{' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(r))}'/>"
    g += [pl(s, INK, 6), pl(a, GOLD, 7)]
    g.append(f"<text x='{x(n)+14:.1f}' y='{y(a[-1])+12:.1f}' font-size='38' font-weight='800' fill='{GOLD}'>{money(a[-1])}</text>")
    g.append(f"<text x='{x(n)+14:.1f}' y='{y(s[-1])+12:.1f}' font-size='38' font-weight='800' fill='{INK}'>{money(s[-1])}</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(g)}</svg>"
def card2(b):
    key = (f"<div style='display:flex;gap:40px;font:800 32px/1 BC;letter-spacing:2px;text-transform:uppercase;margin:30px 0 26px'>"
           f"<span><i style='display:inline-block;width:44px;height:9px;border-radius:5px;background:{GOLD};margin-right:12px;vertical-align:middle'></i>Our price</span>"
           f"<span><i style='display:inline-block;width:44px;height:9px;border-radius:5px;background:{INK};margin-right:12px;vertical-align:middle'></i>Betfair SP</span></div>")
    body = f"<div class='hero'>Both lines <span>go up</span></div>{key}{chart(b)}"
    return page("$100 a tip", body)
def card3(b):
    n = len(b); beat = sum(x["taken"] > x["bsp"] for x in b); w = sum(x["won"] for x in b); exp = sum(1 / x["bsp"] for x in b)
    med = statistics.median(x["taken"] / x["bsp"] for x in b)
    s1 = (f"<div class='stat'><div class='big'>{100*beat/n:.0f}%</div><div class='lab'>of tips priced bigger than Betfair SP</div>"
          f"<div class='track'><i style='width:{100*beat/n:.1f}%'></i></div><div class='cap'><span>{beat} of {n}</span><span>Typical tip {med:.1f}x BSP</span></div></div>")
    s2 = (f"<div class='stat'><div class='big'>{w}</div><div class='lab'>winners. Betfair SP said {exp:.0f}.</div>"
          f"<div class='track'><i style='width:{100*w/max(w, exp)*0.95:.1f}%'></i><u style='left:{100*exp/max(w, exp)*0.95:.1f}%'></u></div>"
          f"<div class='cap'><span>Market {exp:.0f}</span><span>Us {w}</span></div></div>")
    return page("Beating the market", f"<div class='hero'>We beat <span>the market</span></div>{s1}{s2}")
async def main(src, outdir):
    from playwright.async_api import async_playwright
    b = json.load(open(src))["bets"]
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=exe); pg = await br.new_page(viewport={"width": 1080, "height": 1350})
        for k, f in (("1-money", card1), ("2-line", card2), ("3-market", card3)):
            await pg.set_content(f(b)); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f"{outdir}/october-{k}.png"); print("ok", k)
        await br.close()
if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
