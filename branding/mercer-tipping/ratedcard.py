"""Mercer Tipping rated-price card (13 Nov 2026, founder: "a picture to post of just rated prices" for the CF Orr):
one race, every runner's saddlecloth number, name and our rated price, shortest first. 1080x1350, tipcard.py's look.
python ratedcard.py RATED.json OUT.png
RATED.json: {"day", "date", "race", "sub", "rows": [{"number", "horse", "rated"}], "brand": true, "footer": "Rated prices."}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS


def card(d):
    n = len(d["rows"]); hs = 58 if n <= 8 else 48 if n <= 12 else 40
    css = TIP_CSS.replace("{hs}", str(hs)) + ".row{grid-template-columns:96px 1fr auto}"
    if n > 12:
        css += ".row{padding:7px 0}.r{font-size:28px;padding:4px 0}"
    brand = d.get("brand", True)
    if not brand:
        css += ".top{justify-content:flex-start}.when{text-align:left}"
    rows = "".join(f"<div class='row'><div><div class='r'>{html.escape(str(x['number']))}</div></div>"
                   f"<div class='h'>{html.escape(x['horse'])}</div><div class='p'>{html.escape(x['rated'])}</div></div>"
                   for x in d["rows"])
    return (f"<html><head><style>{css}</style></head><body>"
            f"<div class='top'><div class='lock'>"
            + ("<div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div>" if brand else "")
            + f"</div><div class='when'>{html.escape(d['day'])}<span>{html.escape(d['date'])}</span></div></div>"
            f"<div class='list'><div class='mtg'><h2>{html.escape(d['race'])}<small>{html.escape(d.get('sub', ''))}</small></h2>{rows}</div></div>"
            + (f"<div class='foot'><span>{html.escape(d.get('footer', 'Rated prices.'))}</span><span>18+ · Gamble responsibly</span></div>" if brand else "")
            + "</body></html>")


async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
