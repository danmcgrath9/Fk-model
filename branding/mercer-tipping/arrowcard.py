"""Mercer Tipping price-arrow card (26 Oct 2026, founder: "happy to build multiple?"): winners, each drawn from the price
we tipped (gold) down to where Betfair SP had them (white), on one log price scale; a headline and one honest line under.
1080x1350, tipcard.py's look.   python arrowcard.py ARROW.json OUT.png
ARROW.json: {"title", "sub", "head", "rows": [{"horse", "where", "taken", "bsp"}], "line"}"""
import asyncio, glob, html, json, math, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.head{{font:800 64px/1.02 BC;text-transform:uppercase;margin:34px 0 22px}} .head span{{color:{GOLD}}}
svg{{display:block;margin:0}} svg text{{font-family:BC}}
.line{{font:600 34px/1.25 BC;color:{PALE};margin-top:20px}} .line b{{color:{INK}}}
"""
def chart(rows, W=936):
    RH = 86; H = RH * len(rows) + 50; L, R = 300, 48
    lo, hi = math.log(1.6), math.log(18)
    x = lambda p: L + (math.log(min(max(p, 1.6), 18)) - lo) / (hi - lo) * (W - L - R)
    s = []
    for p in (2, 3, 5, 8, 12):
        s.append(f"<line x1='{x(p):.1f}' x2='{x(p):.1f}' y1='0' y2='{H-40}' stroke='{LINE}' stroke-width='2'/>"
                 f"<text x='{x(p):.1f}' y='{H-8}' text-anchor='middle' font-size='26' font-weight='600' fill='{PALE}'>${p}</text>")
    fm = lambda p: f"${p:g}" if p == int(p) else f"${p:.2f}"
    for i, r in enumerate(rows):
        cy = i * RH + RH / 2; a, b = x(r["taken"]), x(r["bsp"])
        s.append(f"<text x='0' y='{cy-4:.1f}' font-size='36' font-weight='800' fill='{INK}'>{html.escape(r['horse'].upper())}</text>"
                 f"<text x='0' y='{cy+26:.1f}' font-size='22' font-weight='600' fill='{PALE}' letter-spacing='2'>{html.escape(r.get('where','').upper())}</text>")
        s.append(f"<line x1='{a:.1f}' x2='{b+14:.1f}' y1='{cy:.1f}' y2='{cy:.1f}' stroke='{GOLD}' stroke-width='6'/>"
                 f"<polygon points='{b+2:.1f},{cy:.1f} {b+20:.1f},{cy-11:.1f} {b+20:.1f},{cy+11:.1f}' fill='{GOLD}'/>"
                 f"<circle cx='{b:.1f}' cy='{cy:.1f}' r='9' fill='{INK}'/><circle cx='{a:.1f}' cy='{cy:.1f}' r='12' fill='{GOLD}'/>"
                 f"<text x='{a:.1f}' y='{cy-22:.1f}' text-anchor='middle' font-size='30' font-weight='800' fill='{GOLD}'>{fm(r['taken'])}</text>"
                 f"<text x='{b:.1f}' y='{cy+40:.1f}' text-anchor='middle' font-size='26' font-weight='600' fill='{INK}'>{fm(r['bsp'])}</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(s)}</svg>"
def card(d):
    key = (f"<div style='display:flex;gap:34px;font:800 28px/1 BC;letter-spacing:2px;text-transform:uppercase;margin-bottom:18px'>"
           f"<span><i style='display:inline-block;width:22px;height:22px;border-radius:50%;background:{GOLD};margin-right:10px;vertical-align:-3px'></i>We tipped</span>"
           f"<span><i style='display:inline-block;width:18px;height:18px;border-radius:50%;background:{INK};margin-right:10px;vertical-align:-2px'></i>Betfair SP</span></div>")
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='head'>{d['head']}</div>{key}{chart(d['rows'])}<div class='line'>{d['line']}</div><div style='flex:1'></div>"
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
