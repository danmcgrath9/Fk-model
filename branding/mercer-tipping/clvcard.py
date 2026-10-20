"""Mercer Tipping closing-line card: each bet's taken price against BSP as a bar (percent above or below BSP),
1080x1350, tipcard.py's look.   python clvcard.py CLV.json OUT.png
CLV.json: {"title", "sub", "note", "footer", "bets": [{"horse", "day", "taken", "bsp"}]}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
RED = "#e0645a"

CSS = TIP_CSS.replace("{hs}", "40") + f"""
.hl{{display:flex;gap:18px;margin:34px 0 22px}} .hl div{{flex:1;border:2px solid {LINE};border-radius:10px;padding:14px;text-align:center}}
.hl b{{display:block;font:800 60px/1 BC;color:{GOLD}}} .hl span{{display:block;font:600 20px/1.1 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:8px}}
.ch{{display:flex;flex-direction:column}}
.br{{display:grid;grid-template-columns:270px 1fr 96px;align-items:center;column-gap:14px;height:{{rh}}px}}
.br .n{{font:800 {{fs}}px/1 BC;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.br .n small{{font:600 {{ss}}px/1 BC;color:{PALE};letter-spacing:1px;margin-left:8px}}
.br .tr{{position:relative;height:60%}} .br .z{{position:absolute;top:-4px;bottom:-4px;width:2px;background:{PALE}}}
.br .bar{{position:absolute;top:0;bottom:0;border-radius:3px}}
.br .v{{font:800 {{fs}}px/1 BC;text-align:right}}
.note{{font:600 26px/1.35 BC;color:{INK};letter-spacing:1px;margin-top:18px}} .note b{{color:{GOLD}}}
"""


def card(d):
    bets = sorted(d["bets"], key=lambda b: -(b["taken"] / b["bsp"]))
    pcts = [b["taken"] / b["bsp"] - 1 for b in bets]
    lo, hi = min(min(pcts), -0.2), max(pcts)
    z = -lo / (hi - lo) * 100   # zero line position in % of the track
    n = len(bets); rh = 34 if n <= 26 else 30
    css = CSS.replace("{rh}", str(rh)).replace("{fs}", "26" if n <= 26 else "23").replace("{ss}", "17")
    rows = ""
    for b, p in zip(bets, pcts):
        w = abs(p) / (hi - lo) * 100; left = z if p >= 0 else z - w
        col = GOLD if p > 0.005 else RED if p < -0.005 else PALE
        rows += (f"<div class='br'><div class='n'>{html.escape(b['horse'])}<small>{html.escape(b['day'])}</small></div>"
                 f"<div class='tr'><div class='z' style='left:{z:.1f}%'></div><div class='bar' style='left:{left:.1f}%;width:{w:.1f}%;background:{col}'></div></div>"
                 f"<div class='v' style='color:{col}'>{'0%' if abs(p) < 0.005 else format(p, '+.0%')}</div></div>")
    beat = sum(p > 0 for p in pcts); avg = sum(b['taken'] / b['bsp'] for b in bets) / n - 1
    med = sorted(pcts)[n // 2] if n % 2 else (sorted(pcts)[n // 2 - 1] + sorted(pcts)[n // 2]) / 2
    hl = (f"<div><b>{beat} / {n}</b><span>Beat BSP</span></div><div><b>{avg:+.0%}</b><span>Average above BSP</span></div>"
          f"<div><b>{med:+.0%}</b><span>Typical (median) bet</span></div>")
    return (f"<html><head><style>{css}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='hl'>{hl}</div><div class='ch'>{rows}</div><div class='note'>{d.get('note', '')}</div><div style='flex:1'></div>"
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
