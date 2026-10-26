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
.n{{font:600 24px/1.3 BC;color:{PALE};margin-top:30px}}
"""
def bars(vals, lo, hi, W=936, RH=82):
    H = RH * len(vals) + 20; L = 330; R = 120; zero = L + (0 - lo) / (hi - lo) * (W - L - R)
    x = lambda v: L + (v - lo) / (hi - lo) * (W - L - R); s = []
    s.append(f"<line x1='{zero:.1f}' x2='{zero:.1f}' y1='0' y2='{H}' stroke='{INK}' stroke-width='3'/>")
    for i, (g, v) in enumerate(zip(GROUPS, vals)):
        p = (v - 1) * 100; cy = i * RH + RH / 2; a, b = sorted((zero, x(p))); c = RED if p < 0 else GOLD
        hl = i == 0
        s.append(f"<text x='0' y='{cy+11:.1f}' font-size='34' font-weight='{800 if hl else 600}' fill='{INK if hl else PALE}'>{g}</text>")
        s.append(f"<rect x='{a:.1f}' y='{cy-24:.1f}' width='{max(b-a,3):.1f}' height='48' rx='4' fill='{c}'/>")
        tx = x(p) + (14 if p >= 0 else -14); anc = "start" if p >= 0 else "end"
        s.append(f"<text x='{tx:.1f}' y='{cy+13:.1f}' text-anchor='{anc}' font-size='40' font-weight='800' fill='{c}'>{p:+.1f}%</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(s)}</svg>"
def card():
    body = (f"<div class='hero'>World Pool <span>crunches</span> the tote</div>"
            f"<div class='sec'><h3>Favourites: tote v bookie SP</h3><p>Under $5. Below zero = the tote paid less than the bookies.</p>{bars(FAV, -6, 12)}</div>"
            f"<div class='sec'><h3>Tote v Betfair SP</h3><p>Every price. How far the tote sits under Betfair.</p>{bars(BSP, -26, 6)}</div>"
            f"<div class='n'>Median prices on the same runners · 12,527 runs, 2022 to 2026 · World Pool days 349 runs</div>")
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
