"""Mercer Tipping tip card: one image a day, the bets by meeting, 1080x1350 (Instagram/X portrait).
python tipcard.py CARD.json OUT.png
CARD.json: {"day": "Friday", "date": "9 Oct", "meetings": [{"name": "Ballarat", "note": "Good 4",
            "bets": [{"race": 5, "horse": "Old Time Rock", "price": "$17", "units": "0.5u"}]}]}"""
import asyncio, base64, glob, html, json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
f = lambda n: base64.b64encode(open(os.path.join(here, n), 'rb').read()).decode()
NAVY, INK, GOLD, PALE, LINE = "#13233a", "#ffffff", "#e0b04a", "#9fb0c8", "#2a3d5a"
CSS = f"""@font-face{{font-family:BC;font-weight:800;src:url(data:font/woff2;base64,{f('BarlowCondensed-800.woff2')}) format('woff2')}}
@font-face{{font-family:BC;font-weight:600;src:url(data:font/woff2;base64,{f('BarlowCondensed-600.woff2')}) format('woff2')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1350px;background:{NAVY};color:{INK};font-family:BC;display:flex;flex-direction:column;padding:64px 72px 52px}}
.top{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:6px solid {GOLD};padding-bottom:22px}}
.brand{{font:800 54px/0.9 BC;letter-spacing:2px}} .brand span{{display:block;font:600 22px/1 BC;color:{GOLD};letter-spacing:11px;margin-top:10px}}
.when{{text-align:right;font:800 92px/0.85 BC;text-transform:uppercase}} .when span{{display:block;font:600 30px/1 BC;color:{PALE};letter-spacing:6px;margin-top:10px}}
.list{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px}}
.mtg h2{{display:flex;align-items:baseline;gap:18px;font:800 40px/1 BC;color:{GOLD};text-transform:uppercase;letter-spacing:5px;margin-bottom:6px}}
.mtg h2 small{{font:600 24px/1 BC;color:{PALE};letter-spacing:3px}}
.row{{display:grid;grid-template-columns:96px 1fr auto 150px;align-items:center;column-gap:22px;padding:14px 0;border-bottom:2px solid {LINE}}}
.r{{font:800 34px/1 BC;color:{NAVY};background:{GOLD};border-radius:8px;text-align:center;padding:8px 0}}
.h{{font:800 {{hs}}px/1 BC;text-transform:uppercase;letter-spacing:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.p{{font:800 {{hs}}px/1 BC;color:{GOLD};text-align:right}}
.u{{font:600 30px/1 BC;color:{INK};text-align:right;letter-spacing:2px;border-left:2px solid {LINE};padding-left:18px}}
.foot{{display:flex;justify-content:space-between;font:600 24px/1.2 BC;color:{PALE};letter-spacing:2px;border-top:2px solid {LINE};padding-top:22px}}
"""
def card(d):
    n = sum(len(m["bets"]) for m in d["meetings"]); hs = 58 if n <= 6 else 48 if n <= 9 else 40
    rows = []
    for m in d["meetings"]:
        b = "".join(f"<div class='row'><div class='r'>R{x['race']}</div><div class='h'>{html.escape(x['horse'])}</div>"
                    f"<div class='p'>{html.escape(x['price'])}</div><div class='u'>{html.escape(x['units'])} WIN</div></div>" for x in m["bets"])
        rows.append(f"<div class='mtg'><h2>{html.escape(m['name'])}<small>{html.escape(m.get('note',''))}</small></h2>{b}</div>")
    return (f"<html><head><style>{CSS.replace('{hs}', str(hs))}</style></head><body>"
            f"<div class='top'><div class='brand'>MERCER<span>TIPPING</span></div><div class='when'>{html.escape(d['day'])}<span>{html.escape(d['date'])}</span></div></div>"
            f"<div class='list'>{''.join(rows)}</div>"
            f"<div class='foot'><span>{html.escape(d.get('footer','Prices at time of posting. Win bets.'))}</span><span>18+ · Gamble responsibly</span></div></body></html>")
async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()
if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
