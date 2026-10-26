"""Mercer Tipping card: Flemington Sat 24 Oct 2026 (Cox Plate day), every winner's tote dividend against bookie SP
(26 Oct 2026, founder: "create me a graph and story"). Data from scripts/meeting_tote.py. 1080x1350, tipcard.py's look.
python flemtote.py OUT.png"""
import asyncio, glob, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
RED = "#e0645a"
W9 = [("R1", "Stokke", 18.00, 18.35), ("R2", "Buggsy", 3.40, 3.20), ("R3", "True Rebel", 2.60, 2.40), ("R4", "Caddington", 12.00, 10.85),
      ("R5", "Smooth Chino", 8.50, 7.15), ("R6", "Surfin' Bird", 3.00, 2.35), ("R7", "Juja Kibo", 7.50, 6.30),
      ("R8", "Cosmic Crusader", 9.50, 8.15), ("R9", "Soverato", 4.80, 4.55)]
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.hero{{font:800 72px/0.98 BC;text-transform:uppercase;margin:34px 0 6px}} .hero span{{color:{RED}}}
.sub2{{font:600 32px/1.2 BC;color:{PALE};margin:4px 0 26px}}
svg text{{font-family:BC}} svg{{display:block}}
.foot2{{font:600 30px/1.3 BC;color:{PALE};margin-top:22px}} .foot2 b{{color:{INK}}}
"""
fm = lambda p: f"${p:.2f}"
def chart(W=936, RH=76):
    H = RH * len(W9) + 10; L = 350; R = 20; zero = L + (W - L - R) * 0.72; sc = (W - L - R) * 0.72 / 25
    s = [f"<line x1='{zero:.1f}' x2='{zero:.1f}' y1='0' y2='{H}' stroke='{INK}' stroke-width='3'/>"]
    for i, (rc, h, sp, tote) in enumerate(W9):
        p = (tote / sp - 1) * 100; cy = i * RH + RH / 2; c = RED if p < 0 else GOLD; x1 = zero + p * sc; a, b = sorted((zero, x1))
        s.append(f"<text x='0' y='{cy+4:.1f}' font-size='32' font-weight='800' fill='{INK}'>{h.upper()}</text>"
                 f"<text x='0' y='{cy+30:.1f}' font-size='22' font-weight='600' fill='{PALE}'>{rc} · SP {fm(sp)} · tote {fm(tote)}</text>"
                 f"<rect x='{a:.1f}' y='{cy-20:.1f}' width='{max(b-a,3):.1f}' height='40' rx='4' fill='{c}'/>")
        tx, anc = (x1 - 12, "end") if p < 0 else (x1 + 12, "start")
        s.append(f"<text x='{tx:.1f}' y='{cy+12:.1f}' text-anchor='{anc}' font-size='34' font-weight='800' fill='{c}'>{p:+.0f}%</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(s)}</svg>"
def card():
    body = (f"<div class='hero'>8 of 9 winners <span>paid less</span> on the tote</div>"
            f"<div class='sub2'>Flemington, Cox Plate day. Tote dividend against bookie SP.</div>{chart()}"
            f"<div class='foot2'><b>World Pool days:</b> 44% of winners pay under SP. <b>Normal meetings:</b> 21%.</div>")
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>Saturday<span>24 October</span></div></div>{body}<div style='flex:1'></div>"
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
