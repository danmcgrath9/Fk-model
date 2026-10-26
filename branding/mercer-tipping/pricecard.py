"""Mercer Tipping clean price card (26 Oct 2026, founder: "cleaner design so I can see"): a few winners, the price we
tipped beside the Betfair SP, big type, no chart, one line under. 1080x1350, tipcard.py's look.
python pricecard.py PRICES.json OUT.png    PRICES.json: {"title", "sub", "head", "rows": [{"horse", "taken", "bsp"}], "line"}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.head{{font:800 76px/1 BC;text-transform:uppercase;margin:44px 0 34px}} .head span{{color:{GOLD}}}
.phd,.pr{{display:grid;grid-template-columns:1fr 190px 60px 190px;align-items:center}}
.phd{{font:600 22px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;padding-bottom:14px;border-bottom:3px solid {GOLD}}}
.phd span:not(:first-child),.pr div:not(:first-child){{text-align:right}} .phd span:nth-child(3),.pr div:nth-child(3){{text-align:center}}
.pr{{height:118px;border-bottom:2px solid {LINE}}}
.pr .ph{{font:800 50px/1 BC;text-transform:uppercase;white-space:nowrap}} .pr .pt{{font:800 66px/1 BC;color:{GOLD};font-variant-numeric:tabular-nums}}
.pr .pa{{font:800 44px/1 BC;color:{PALE}}} .pr .ps{{font:600 52px/1 BC;color:{PALE};font-variant-numeric:tabular-nums}}
.line{{font:600 36px/1.25 BC;color:{PALE};margin-top:34px}} .line b{{color:{INK}}}
"""
fm = lambda p: f"${p:g}" if p == int(p) else f"${p:.2f}"
def card(d):
    rows = "".join(f"<div class='pr'><div class='ph'>{html.escape(r['horse'])}</div><div class='pt'>{fm(r['taken'])}</div>"
                   f"<div class='pa'>→</div><div class='ps'>{fm(r['bsp'])}</div></div>" for r in d["rows"])
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='head'>{d['head']}</div><div class='phd'><span>Winner</span><span>We tipped</span><span></span><span>Betfair SP</span></div>"
            f"{rows}<div class='line'>{d['line']}</div><div style='flex:1'></div>"
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
