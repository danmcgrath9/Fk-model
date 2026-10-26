"""Mercer Tipping profit-line card (26 Oct 2026, founder: "show how we are profitable at BSP even without prices tipped
early ... where's charts"): every tip at 1u in date order, running profit at the price we tipped (gold) and at Betfair SP
(white), three boxes on top, 1080x1350, tipcard.py's look.
python profitline.py PROFIT.json OUT.png    PROFIT.json: {"title", "sub", "bets": [{"horse", "date", "taken", "bsp", "won"}]}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.hl{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:34px 0 26px}} .hl div{{border:2px solid {LINE};border-radius:10px;padding:16px 10px;text-align:center}}
.hl b{{display:block;font:800 64px/1 BC;color:{GOLD};font-variant-numeric:tabular-nums}} .hl b.w{{color:{INK}}}
.hl span{{display:block;font:600 21px/1.15 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:10px}}
.key{{display:flex;gap:34px;font:800 30px/1 BC;letter-spacing:2px;text-transform:uppercase;margin:22px 0 0}} .key i{{display:inline-block;width:40px;height:8px;border-radius:4px;margin-right:12px;vertical-align:middle}}
svg text{{font-family:BC;font-weight:600}}
"""
def run(bets, key):
    c, out = 0.0, [0.0]
    for b in bets: c += (b[key] - 1) if b["won"] else -1; out.append(c)
    return out
def chart(bets, W=936, H=760):
    a, s_ = run(bets, "taken"), run(bets, "bsp"); n = len(a) - 1
    top = max(max(a), max(s_)); bot = min(min(a), min(s_), 0)
    step = 20 if top < 160 else 40; hi = step * (int(top // step) + 1); lo = -step * (int(-bot // step) + (1 if bot < 0 else 0))
    L, R, T, B = 92, 70, 14, 46
    x = lambda i: L + i * (W - L - R) / n; y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    g = []
    v = lo
    while v <= hi:
        g.append(f"<line x1='{L}' x2='{W-R}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='{INK if v == 0 else LINE}' stroke-width='{3 if v == 0 else 2}'/>"
                 f"<text x='{L-14}' y='{y(v)+9:.1f}' text-anchor='end' font-size='26' fill='{PALE}'>{'+' if v > 0 else ''}{v:g}u</text>"); v += step
    done = set()
    for t in (5, 12, 19, 26):
        i = next((i for i, b in enumerate(bets) if b["date"] >= t), None)
        if i is not None and bets[i]["date"] not in done:
            done.add(bets[i]["date"]); g.append(f"<text x='{x(i):.1f}' y='{H-10}' text-anchor='middle' font-size='24' fill='{PALE}'>{bets[i]['date']} Oct</text>")
    pl = lambda r, c, w: f"<polyline fill='none' stroke='{c}' stroke-width='{w}' stroke-linejoin='round' points='{' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(r))}'/>"
    lab = lambda r, c: f"<text x='{x(n)+10:.1f}' y='{y(r[-1])+10:.1f}' font-size='30' font-weight='800' fill='{c}'>{r[-1]:+.0f}u</text>"
    g += [pl(s_, INK, 5), pl(a, GOLD, 6), lab(a, GOLD), lab(s_, INK)]
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(g)}</svg>"
def card(d):
    b = d["bets"]; n = len(b); w = sum(x["won"] for x in b); a, s_ = run(b, "taken")[-1], run(b, "bsp")[-1]
    hl = (f"<div><b>{w} / {n}</b><span>Winners</span></div><div><b>{100*a/n:+.0f}%</b><span>At our price</span></div>"
          f"<div><b class='w'>{100*s_/n:+.0f}%</b><span>At Betfair SP</span></div>")
    key = f"<div class='key'><span><i style='background:{GOLD}'></i>Our price</span><span><i style='background:{INK}'></i>Betfair SP</span></div>"
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='hl'>{hl}</div>{key}{chart(b)}<div style='flex:1'></div>"
            f"<div class='foot'><span>Win bets.</span><span>18+ · Gamble responsibly</span></div></body></html>")
async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()
if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
