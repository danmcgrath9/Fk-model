"""Mercer Tipping closing-line card for a whole month (25 Oct 2026, founder: "the BSP graph ... all October tips"): every
bet as one column, taken price (after deductions) over Betfair SP on a log scale, sorted best to worst, gold above BSP,
red below; three boxes and the best three in an aligned table. 1080x1350, tipcard.py's look.
python clvmonth.py CLV.json OUT.png    CLV.json: {"title", "sub", "bets": [{"horse", "date", "taken", "bsp"}]}"""
import asyncio, glob, html, json, math, statistics, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
RED = "#e0645a"
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.hl{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:34px 0 18px}} .hl div{{border:2px solid {LINE};border-radius:10px;padding:14px;text-align:center}}
.hl b{{display:block;font:800 60px/1 BC;color:{GOLD};font-variant-numeric:tabular-nums}} .hl span{{display:block;font:600 20px/1.1 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:8px}}
svg text{{font-family:BC;font-weight:600}}
.wt{{font:800 30px/1 BC;color:{GOLD};letter-spacing:5px;text-transform:uppercase;margin:18px 0 4px}}
.w{{display:grid;grid-template-columns:1fr 120px 40px 120px 120px;align-items:baseline;column-gap:10px;padding:10px 0;border-bottom:2px solid {LINE}}}
.w .h{{font:800 36px/1 BC;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.w .n{{font:800 36px/1 BC;text-align:right;font-variant-numeric:tabular-nums}} .w .v{{font:600 24px/1 BC;color:{PALE};text-align:center}} .w .g{{color:{GOLD}}}
"""
def chart(bets, W=936, H=610):
    r = sorted((b["taken"] / b["bsp"] for b in bets), reverse=True)
    lo, hi = math.log(1/3), math.log(4.0); L, R, T, B = 104, 8, 14, 14
    y = lambda v: T + (hi - math.log(min(max(v, 1/3), 4.0))) / (hi - lo) * (H - T - B)
    bw = (W - L - R) / len(r); s = []
    for k in (4, 3, 2, 1.5, 0.67, 0.5, 0.33):
        s.append(f"<line x1='{L}' x2='{W-R}' y1='{y(k):.1f}' y2='{y(k):.1f}' stroke='{LINE}' stroke-width='2'/>"
                 f"<text x='{L-14}' y='{y(k)+9:.1f}' text-anchor='end' font-size='26' fill='{PALE}'>{k:g}x</text>")
    for i, v in enumerate(r):
        y0, y1 = sorted((y(1), y(v))); c = GOLD if v > 1 else RED
        s.append(f"<rect x='{L + i*bw + 1:.1f}' y='{y0:.1f}' width='{max(bw-2, 1):.1f}' height='{max(y1-y0, 2):.1f}' fill='{c}'/>")
    s.append(f"<line x1='{L}' x2='{W-R}' y1='{y(1):.1f}' y2='{y(1):.1f}' stroke='{INK}' stroke-width='3'/>"
             f"<text x='{L-14}' y='{y(1)+10:.1f}' text-anchor='end' font-size='30' font-weight='800' fill='{INK}'>BSP</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(s)}</svg>"
def card(d):
    b = d["bets"]; n = len(b); r = [x["taken"] / x["bsp"] for x in b]; beat = sum(v > 1 for v in r)
    hl = (f"<div><b>{beat} / {n}</b><span>Beat BSP</span></div><div><b>{100*beat/n:.0f}%</b><span>Of bets</span></div>"
          f"<div><b>{statistics.median(r):.2f}x</b><span>Typical price v BSP</span></div>")
    top = sorted(b, key=lambda x: -x["taken"] / x["bsp"])[:3]
    fm = lambda p: f"${p:g}" if p == int(p) else f"${p:.2f}"
    rows = "".join(f"<div class='w'><div class='h'>{html.escape(x['horse'])}</div><div class='n g'>{fm(x['taken'])}</div><div class='v'>v</div>"
                   f"<div class='n'>{fm(x['bsp'])}</div><div class='n g'>{x['taken']/x['bsp']:.1f}x</div></div>" for x in top)
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='hl'>{hl}</div>{chart(b)}<div class='wt'>Best three</div>{rows}<div style='flex:1'></div>"
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
