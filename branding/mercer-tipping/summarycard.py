"""Mercer Tipping run summary: days, bets, profit and how often our price beat BSP, 1080x1350, tipcard.py's look.
python summarycard.py SUMMARY.json OUT.png"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE

CSS = TIP_CSS.replace("{hs}", "40") + f"""
.big{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:54px 0 44px}}
.big div{{border:2px solid {LINE};border-radius:10px;padding:20px 18px;text-align:center}}
.big b{{display:block;font:800 72px/1 BC;color:{GOLD}}} .big span{{display:block;font:600 22px/1.15 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:10px}}
.tb .hd,.tb .rw{{display:grid;grid-template-columns:2.3fr 0.6fr 0.6fr 0.9fr 1fr 1fr;align-items:center;column-gap:12px}}
.tb .hd{{font:600 21px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;padding-bottom:12px;border-bottom:3px solid {GOLD}}}
.tb .rw{{height:104px;border-bottom:2px solid {LINE};font:800 34px/1 BC}}
.tb .rw div:nth-child(n+2),.tb .hd span:nth-child(n+2){{text-align:right}}
.tb .rw .d{{text-transform:uppercase;letter-spacing:1px}} .tb .rw .d small{{display:block;font:600 20px/1.1 BC;color:{PALE};letter-spacing:2px;margin-top:6px;white-space:nowrap}}
.tb .rw .g{{color:{GOLD}}} .tb .tot{{border-bottom:0;border-top:3px solid {GOLD}}}
.note{{font:600 32px/1.35 BC;color:{INK};letter-spacing:1px;margin-top:44px}} .note b{{color:{GOLD}}}
"""


def card(d):
    rows = "".join(
        f"<div class='rw{' tot' if r.get('total') else ''}'><div class='d'>{html.escape(r['day'])}<small>{html.escape(r.get('where', ''))}</small></div>"
        f"<div>{r['bets']}</div><div>{r['won']}</div><div>{html.escape(r['staked'])}</div><div class='g'>{html.escape(r['profit'])}</div>"
        f"<div>{html.escape(r['bsp'])}</div></div>" for r in d["rows"])
    big = "".join(f"<div><b>{html.escape(b['v'])}</b><span>{html.escape(b['k'])}</span></div>" for b in d["big"])
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='big'>{big}</div>"
            f"<div class='tb'><div class='hd'><span>Day</span><span>Bets</span><span>Won</span><span>Staked</span><span>Profit</span><span>Beat BSP</span></div>{rows}</div>"
            f"<div class='note'>{d.get('note', '')}</div><div style='flex:1'></div>"
            f"<div class='foot'><span>{html.escape(d.get('footer', ''))}</span><span>18+ · Gamble responsibly</span></div></body></html>")


async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
