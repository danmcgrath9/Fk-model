"""Mercer Tipping market card: our rated market for one race, 1080x1350 (Instagram/X portrait), same look as tipcard.py.
python marketcard.py CARD.json OUT.png
CARD.json: {"day": "Saturday", "date": "17 October", "race": "Caulfield Cup", "note": "R8 · 2400m · Good 4",
            "runners": [{"horse": "Cosmic Crusader", "barrier": 17, "ours": "$3.75", "market": "$5"}], "market_label": "TAB", "show_market": true}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE

CSS = TIP_CSS.replace("{hs}", "40") + f"""
.list{{justify-content:flex-start;gap:0;margin-top:30px}}
.title{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:14px}}
.title h2{{font:800 56px/1 BC;color:{GOLD};text-transform:uppercase;letter-spacing:4px}}
.title small{{font:600 24px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase}}
.hd,.mr{{display:grid;grid-template-columns:70px 1fr 150px 130px;align-items:center;column-gap:18px}}
.nomkt .hd,.nomkt .mr{{grid-template-columns:70px 1fr 170px}}
.hd{{font:600 20px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;padding:0 0 10px;border-bottom:3px solid {GOLD}}}
.hd span:nth-child(n+3),.mr div:nth-child(n+3){{text-align:right}}
.mr{{padding:0;height:{{rh}}px;border-bottom:2px solid {LINE}}}
.mr .b{{font:600 24px/1 BC;color:{PALE};letter-spacing:1px}}
.mr .n{{font:800 {{fs}}px/1 BC;text-transform:uppercase;letter-spacing:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.mr .o{{font:800 {{fs}}px/1 BC;color:{GOLD}}}
.mr .m{{font:600 {{ms}}px/1 BC;color:{PALE}}}
.mr.top .n,.mr.top .o{{font-size:{{tfs}}px}}
"""


def card(d):
    rs = d["runners"]; n = len(rs); show = d.get("show_market", True)
    rh = 52 if n <= 18 else 46 if n <= 22 else 40
    fs = 34 if n <= 18 else 30
    css = CSS.replace("{rh}", str(rh)).replace("{fs}", str(fs)).replace("{ms}", str(fs - 6)).replace("{tfs}", str(fs + 6))
    rows = "".join(
        f"<div class='mr{' top' if i == 0 else ''}'><div class='b'>{r.get('barrier') or ''}</div>"
        f"<div class='n'>{html.escape(r['horse'])}</div><div class='o'>{html.escape(r['ours'])}</div>"
        + (f"<div class='m'>{html.escape(r.get('market') or '-')}</div>" if show else "") + "</div>" for i, r in enumerate(rs))
    label = f"<span>{html.escape(d.get('market_label', 'Market'))}</span>" if show else ""
    return (f"<html><head><style>{css}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['day'])}<span>{html.escape(d['date'])}</span></div></div>"
            f"<div class='list{'' if show else ' nomkt'}'><div class='title'><h2>{html.escape(d['race'])}</h2><small>{html.escape(d.get('note', ''))}</small></div>"
            f"<div class='hd'><span>{html.escape(d.get('first_col', 'Gate'))}</span><span>Our market</span><span>Ours</span>{label}</div>{rows}</div>"
            f"<div class='foot'><span>{html.escape(d.get('footer', 'Our rated prices, not a bet on every runner.'))}</span><span>18+ · Gamble responsibly</span></div></body></html>")


async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
