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
.n{{font:600 24px/1.3 BC;color:{PALE};margin-top:26px}}
.flem{{font:600 36px/1.25 BC;color:{PALE};margin:18px 0 0}} .flem b{{color:{RED};font-weight:800}}
.sub2{{font:600 32px/1.2 BC;color:{PALE};margin:6px 0 22px}}
.key{{display:flex;flex-wrap:wrap;gap:12px 30px;font:800 28px/1 BC;margin-bottom:20px}}
"""
GROUPS = ["World Pool days", "Other metro Saturdays", "All other meetings"]
UNDER = [44, 33, 21]                 # % of winners whose tote paid under bookie SP (scripts/world_pool_tote.py, winners only)
VBSP = [0.824, 0.899, 0.922]         # winners: median tote / Betfair SP
COL = [RED, PALE, GOLD]
def hbars(vals, fmt, mx, W=936, RH=84):
    H = RH * len(vals); L = 330; R = 130; s = []
    for i, (g, v) in enumerate(zip(GROUPS, vals)):
        cy = i * RH + RH / 2; w = (W - L - R) * abs(v) / mx
        s.append(f"<text x='0' y='{cy+11:.1f}' font-size='34' font-weight='{800 if i == 0 else 600}' fill='{INK if i == 0 else PALE}'>{g}</text>"
                 f"<rect x='{L}' y='{cy-24:.1f}' width='{w:.1f}' height='48' rx='4' fill='{COL[i]}'/>"
                 f"<text x='{L+w+14:.1f}' y='{cy+14:.1f}' font-size='42' font-weight='800' fill='{COL[i]}'>{fmt(v)}</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(s)}</svg>"
def card():
    body = (f"<div class='hero'>World Pool <span>crunches</span> the winners</div>"
            f"<div class='flem'><b>8 of 9</b> Flemington winners on Saturday paid less on the tote than the bookies' SP.</div>"
            f"<div class='sec'><h3>Winners paid under bookie SP</h3>{hbars(UNDER, lambda v: f'{v}%', 50)}</div>"
            f"<div class='sec'><h3>Winners: tote under Betfair SP</h3>{hbars([(1-v)*100 for v in VBSP], lambda v: f'-{v:.0f}%', 20)}</div>"
            f"<div class='n'>Tote dividends on 1,532 winners, 2022 to 2026 · World Pool days 32 winners</div>")
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>World Pool<span>Tote v SP v BSP</span></div></div>{body}<div style='flex:1'></div>"
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
