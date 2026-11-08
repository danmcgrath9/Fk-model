"""Mercer Tipping running-profit card (8 Nov 2026, founder: "So make a card or some images"): the Twitter record's profit
in units, race day by race day, as posted (half units, the card's price), three boxes on top, 1080x1350, tipcard.py's look.
python dayline.py DAYS.json OUT.png    DAYS.json: {"title", "sub", "boxes": [{"v", "k"}], "days": [{"d": "17 Oct", "pl": 31.4}],
"ticks": ["17 Oct", ...]}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.hl{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:44px 0 34px}} .hl div{{border:2px solid {LINE};border-radius:10px;padding:18px 10px;text-align:center}}
.hl b{{display:block;font:800 66px/1 BC;color:{GOLD};font-variant-numeric:tabular-nums}}
.hl span{{display:block;font:600 21px/1.15 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:10px}}
.cap{{font:600 24px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;margin:0 0 10px}}
svg text{{font-family:BC;font-weight:600}}
"""
def chart(days, ticks, W=936, H=720):
    c, run = 0.0, [0.0]
    for x_ in days: c += x_["pl"]; run.append(c)
    n = len(run) - 1; top = max(run); bot = min(min(run), 0)
    step = 25 if top < 150 else 50; hi = step * (int(top // step) + 1); lo = -step * (int(-bot // step) + (1 if bot < 0 else 0))
    L, R, T, B = 96, 96, 14, 50
    x = lambda i: L + i * (W - L - R) / n; y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    g, v = [], lo
    while v <= hi:
        g.append(f"<line x1='{L}' x2='{W-R}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='{INK if v == 0 else LINE}' stroke-width='{3 if v == 0 else 2}'/>"
                 f"<text x='{L-14}' y='{y(v)+9:.1f}' text-anchor='end' font-size='26' fill='{PALE}'>{'+' if v > 0 else ''}{v:g}u</text>"); v += step
    for i, x_ in enumerate(days, 1):
        if x_["d"] in ticks:
            g.append(f"<text x='{x(i):.1f}' y='{H-12}' text-anchor='middle' font-size='24' fill='{PALE}'>{html.escape(x_['d'])}</text>")
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(run))
    g.append(f"<polygon fill='{GOLD}' fill-opacity='0.10' points='{x(0):.1f},{y(0):.1f} {pts} {x(n):.1f},{y(0):.1f}'/>")
    g.append(f"<polyline fill='none' stroke='{GOLD}' stroke-width='6' stroke-linejoin='round' points='{pts}'/>")
    g += [f"<circle cx='{x(i):.1f}' cy='{y(v):.1f}' r='5' fill='{GOLD}'/>" for i, v in enumerate(run) if i]
    g.append(f"<text x='{x(n)+12:.1f}' y='{y(run[-1])+10:.1f}' font-size='32' font-weight='800' fill='{GOLD}'>{run[-1]:+.0f}u</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(g)}</svg>"
def card(d):
    hl = "".join(f"<div><b>{html.escape(b['v'])}</b><span>{html.escape(b['k'])}</span></div>" for b in d["boxes"])
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='hl'>{hl}</div><div class='cap'>{html.escape(d.get('cap', 'Running profit, race day by race day'))}</div>"
            f"{chart(d['days'], d.get('ticks', []))}<div style='flex:1'></div>"
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
