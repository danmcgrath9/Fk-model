"""Mercer Tipping winners-v-market card (26 Oct 2026): every tip as a dot (gold = won), our winners against how many
Betfair SP expected, 1080x1350, tipcard.py's look.   python dotcard.py DOTS.json OUT.png
DOTS.json: {"title", "sub", "n", "won", "expected", "head", "line"}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.head{{font:800 64px/1.02 BC;text-transform:uppercase;margin:34px 0 28px}} .head span{{color:{GOLD}}}
.dots{{display:grid;grid-template-columns:repeat(11,1fr);gap:16px 0;justify-items:center;margin:4px 0 34px}}
.dots i{{width:44px;height:44px;border-radius:50%;border:4px solid {LINE};box-sizing:border-box}} .dots i.w{{background:{GOLD};border-color:{GOLD}}}
.vs{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .vs div{{border:2px solid {LINE};border-radius:10px;padding:22px 10px;text-align:center}}
.vs b{{display:block;font:800 104px/1 BC;color:{GOLD}}} .vs b.m{{color:{PALE}}}
.vs span{{display:block;font:600 24px/1.15 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;margin-top:12px}}
.line{{font:600 34px/1.25 BC;color:{PALE};margin-top:30px}} .line b{{color:{INK}}}
"""
def card(d):
    dots = "".join(f"<i class='{'w' if i < d['won'] else ''}'></i>" for i in range(d["n"]))
    vs = (f"<div><b>{d['won']}</b><span>Our winners</span></div>"
          f"<div><b class='m'>{d['expected']}</b><span>Betfair SP expected</span></div>")
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='head'>{d['head']}</div><div class='dots'>{dots}</div><div class='vs'>{vs}</div>"
            f"<div class='line'>{d['line']}</div><div style='flex:1'></div>"
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
