"""Mercer Tipping winner card: one winning bet, big, with its taken price against SP, plus an optional "also on" list.
1080x1350, tipcard.py's look.   python wincard.py WIN.json OUT.png
WIN.json: {"kicker", "horse", "meeting", "date", "stats": [{"v", "k"}], "line", "also_title", "also": [{"race", "horse"}]}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE

CSS = TIP_CSS.replace("{hs}", "58") + f"""
.mid{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px}}
.kick{{font:800 44px/1 BC;color:{GOLD};letter-spacing:8px;text-transform:uppercase}}
.big{{font:800 150px/0.9 BC;text-transform:uppercase;letter-spacing:2px}}
.sub{{font:600 32px/1 BC;color:{PALE};letter-spacing:4px;text-transform:uppercase}}
.st{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.st div{{border:2px solid {LINE};border-radius:10px;padding:18px 10px;text-align:center}}
.st b{{display:block;font:800 60px/1 BC;color:{GOLD}}} .st span{{display:block;font:600 21px/1.1 BC;color:{PALE};letter-spacing:2px;text-transform:uppercase;margin-top:9px}}
.line{{font:600 32px/1.3 BC;color:{INK};letter-spacing:1px}} .line b{{color:{GOLD}}}
.also h2{{font:800 32px/1 BC;color:{GOLD};letter-spacing:5px;text-transform:uppercase;margin-bottom:6px}}
.also .row{{grid-template-columns:96px 1fr;padding:10px 0}} .also .h{{font-size:44px}}
.hero{{display:flex;align-items:center;gap:34px}} .hero svg{{flex:0 0 auto}}
"""

def silks(c):
    """Jockey silks drawn from the colours: {"body", "trim", "sleeves", "cap", "star"} (21 Oct 2026, founder: "see its colours")."""
    b, t, sl, cp, stc = c["body"], c["trim"], c["sleeves"], c["cap"], c.get("star", "#ffffff")
    return (f"<svg width='190' height='230' viewBox='0 0 190 230'>"
            f"<ellipse cx='95' cy='34' rx='36' ry='26' fill='{cp}'/><rect x='56' y='44' width='78' height='10' rx='5' fill='{cp}'/>"
            f"<polygon points='95,16 99,28 112,28 102,35 106,47 95,40 84,47 88,35 78,28 91,28' fill='{stc}'/>"
            f"<path d='M48 80 L10 200 L40 210 L62 120 Z' fill='{sl}'/><path d='M142 80 L180 200 L150 210 L128 120 Z' fill='{sl}'/>"
            f"<path d='M50 70 Q95 58 140 70 L150 225 L40 225 Z' fill='{b}'/>"
            f"<rect x='86' y='72' width='18' height='150' fill='{t}'/><rect x='62' y='108' width='66' height='16' fill='{t}'/>"
            f"<rect x='70' y='150' width='50' height='14' fill='{t}'/></svg>")

def card(d):
    st = "".join(f"<div><b>{html.escape(s['v'])}</b><span>{html.escape(s['k'])}</span></div>" for s in d["stats"])
    also = ""
    if d.get("also"):
        also = (f"<div class='also'><h2>{html.escape(d['also_title'])}</h2>" + "".join(
            f"<div class='row'><div class='r'>R{x['race']}</div><div class='h'>{html.escape(x['horse'])}</div></div>" for x in d["also"]) + "</div>")
    return (f"<html><head><style>{CSS}</style></head><body>"
            "<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>WINNER<span>{html.escape(d['date'])}</span></div></div>"
            f"<div class='mid'><div class='kick'>{html.escape(d['kicker'])}</div><div class='hero'>{silks(d['silks']) if d.get('silks') else ''}<div><div class='big'>{html.escape(d['horse'])}</div>"
            f"<div class='sub' style='margin-top:14px'>{html.escape(d['meeting'])}</div></div></div><div class='st'>{st}</div>"
            f"<div class='line'>{d['line']}</div>{also}</div>"
            "<div class='foot'><span>Win bets at posted prices.</span><span>18+ · Gamble responsibly</span></div></body></html>")

async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
