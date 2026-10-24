"""Mercer Tipping month card for socials (24 Oct 2026, founder: "send me a image that gets my socials going"): one big
profit figure, a row of stats, the biggest winners in an aligned table, a closing line. 1080x1350, tipcard.py's look.
python monthcard.py MONTH.json OUT.png
MONTH.json: {"kicker", "big", "big_sub", "stats": [{"v", "k"}], "wins_title", "wins": [[horse, detail, price, profit]], "end"}
optional "posted" (a line under the stats) and "past_title" + "past": [{"v", "k"}] (a second stats row; 24 Oct 2026, founder:
"that's clearly unsustainable ... say that and then what our past results show")"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "58") + f"""
.mid{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:26px;padding:28px 0 22px}}
.kick{{font:800 40px/1 BC;color:{GOLD};letter-spacing:9px;text-transform:uppercase}}
.big{{font:800 160px/0.85 BC;letter-spacing:1px;color:{GOLD};font-variant-numeric:tabular-nums}}
.bsub{{font:600 34px/1 BC;color:{PALE};letter-spacing:3px;margin-top:12px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);border-top:2px solid {LINE};border-bottom:2px solid {LINE}}}
.st{{padding:18px 0;text-align:center}} .st+.st{{border-left:2px solid {LINE}}}
.st b{{display:block;font:800 64px/1 BC;font-variant-numeric:tabular-nums}} .st span{{display:block;font:600 22px/1.2 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:8px}}
.wt{{font:800 32px/1 BC;color:{GOLD};letter-spacing:5px;text-transform:uppercase;margin-bottom:6px}}
.w{{display:grid;grid-template-columns:1fr 130px 130px;align-items:baseline;column-gap:16px;padding:12px 0;border-bottom:2px solid {LINE}}}
.w .h{{font:800 40px/1 BC;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .w .h small{{font:600 22px/1 BC;color:{PALE};letter-spacing:2px;margin-left:14px}}
.w .n{{font:800 40px/1 BC;text-align:right;font-variant-numeric:tabular-nums}} .w .g{{color:{GOLD}}}
.post{{font:600 30px/1.2 BC;color:{INK};letter-spacing:1px;margin-top:14px}} .post b{{color:{GOLD}}}
.past .stats .st b{{font-size:54px}} .past .stats{{grid-template-columns:repeat(3,1fr)}}
.end{{font:800 50px/1.1 BC;text-transform:uppercase;letter-spacing:1px}} .end span{{color:{GOLD}}}
"""
def card(d):
    stats = "".join(f"<div class='st'><b>{html.escape(s['v'])}</b><span>{html.escape(s['k'])}</span></div>" for s in d["stats"])
    wins = "".join(f"<div class='w'><div class='h'>{html.escape(h)}<small>{html.escape(x)}</small></div><div class='n'>{html.escape(p)}</div><div class='n g'>{html.escape(u)}</div></div>"
                   for h, x, p, u in d["wins"])
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"<div class='mid'><div><div class='kick'>{html.escape(d['kicker'])}</div><div class='big'>{html.escape(d['big'])}</div>"
            f"<div class='bsub'>{html.escape(d['big_sub'])}</div></div><div><div class='stats'>{stats}</div>"
            + (f"<div class='post'>{d['posted']}</div>" if d.get("posted") else "") + "</div>"
            + (f"<div class='past'><div class='wt'>{html.escape(d['past_title'])}</div><div class='stats'>" + "".join(f"<div class='st'><b>{html.escape(s['v'])}</b><span>{html.escape(s['k'])}</span></div>" for s in d["past"]) + "</div></div>" if d.get("past") else "")
            + f"<div><div class='wt'>{html.escape(d['wins_title'])}</div>{wins}</div><div class='end'>{d['end']}</div></div>"
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
