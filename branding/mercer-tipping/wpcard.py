"""Mercer Tipping World Pool card (26 Oct 2026, founder: "a graph showing clearly how fucked the world pool is"): the tote
on World Pool days against ordinary metro Saturdays and other meetings, from scripts/world_pool_tote.py (median price on
the same runs). Two diverging bar groups around zero: favourites' tote v bookie SP, and the tote v Betfair SP.
1080x1350, tipcard.py's look.   python wpcard.py OUT.png"""
import asyncio, glob, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
RED = "#e0645a"
GROUPS = ["World Pool days", "Other metro Saturdays", "All other meetings"]
FAV = [0.974, 1.034, 1.071]      # SP under $5: tote / bookie SP
BSP = [0.822, 0.852, 0.865]      # all prices: tote / Betfair SP
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.hero{{font:800 70px/0.98 BC;text-transform:uppercase;margin:36px 0 4px}} .hero span{{color:{RED}}}
.sec{{margin-top:34px}} .sec h3{{font:800 32px/1 BC;color:{GOLD};letter-spacing:4px;text-transform:uppercase;margin:0 0 6px}}
.sec p{{font:600 26px/1.2 BC;color:{PALE};margin:0 0 20px}}
svg text{{font-family:BC}} svg{{display:block}}
.n{{font:600 24px/1.3 BC;color:{PALE};margin-top:18px}}
.sub2{{font:600 32px/1.2 BC;color:{PALE};margin:6px 0 22px}}
.key{{display:flex;flex-wrap:wrap;gap:12px 30px;font:800 28px/1 BC;margin-bottom:20px}}
"""
BANDS = ["Under $5", "$5 to $13", "$13+", "All runners"]
TOTE = {"World Pool days": [0.974, 1.050, 1.065, 1.045], "Other metro Saturdays": [1.034, 1.059, 1.058, 1.051],
        "All other meetings": [1.071, 1.105, 1.116, 1.100]}   # median tote / bookie SP, scripts/world_pool_tote.py
COL = {"World Pool days": RED, "Other metro Saturdays": PALE, "All other meetings": GOLD}
def grouped(W=936, H=720):
    lo, hi = -4, 14; L, R, T, B = 70, 10, 30, 70
    y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    gw = (W - L - R) / len(BANDS); bw = gw * 0.24; s = []
    for v in range(lo, hi + 1, 2):
        s.append(f"<line x1='{L}' x2='{W-R}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='{INK if v == 0 else LINE}' stroke-width='{3 if v == 0 else 2}'/>"
                 f"<text x='{L-12}' y='{y(v)+9:.1f}' text-anchor='end' font-size='24' font-weight='600' fill='{PALE}'>{v:+d}%</text>")
    for bi, band in enumerate(BANDS):
        gx = L + bi * gw + gw * 0.14
        for k, (g, vals) in enumerate(TOTE.items()):
            p = (vals[bi] - 1) * 100; x0 = gx + k * bw; a, b = sorted((y(0), y(p)))
            s.append(f"<rect x='{x0:.1f}' y='{a:.1f}' width='{bw-6:.1f}' height='{max(b-a,3):.1f}' rx='3' fill='{COL[g]}'/>")
            ty = y(p) - 10 if p >= 0 else y(p) + 30
            s.append(f"<text x='{x0+(bw-6)/2:.1f}' y='{ty:.1f}' text-anchor='middle' font-size='24' font-weight='800' fill='{COL[g]}'>{p:+.1f}</text>")
        s.append(f"<text x='{L+bi*gw+gw/2:.1f}' y='{H-24}' text-anchor='middle' font-size='28' font-weight='800' fill='{INK}'>{band}</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(s)}</svg>"
def card():
    key = "".join(f"<span><i style='display:inline-block;width:26px;height:26px;border-radius:4px;background:{c};margin-right:12px;vertical-align:-5px'></i>{g}</span>" for g, c in COL.items())
    body = (f"<div class='hero'>World Pool <span>crunches</span> the tote</div>"
            f"<div class='sub2'>How much more the tote paid than bookie SP, every runner</div>"
            f"<div class='key'>{key}</div>{grouped()}"
            f"<div class='n'>Median tote / bookie SP on the same runners, by SP band · 12,527 runs 2022 to 2026 · World Pool days 349 runs</div>")
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>World Pool<span>Tote v bookie SP</span></div></div>{body}<div style='flex:1'></div>"
            f"<div class='foot'><span>Win bets.</span><span>18+ · Gamble responsibly</span></div></body></html>")
async def main(out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card()); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()
if __name__ == "__main__":
    asyncio.run(main(sys.argv[1])); print("ok", sys.argv[1])
