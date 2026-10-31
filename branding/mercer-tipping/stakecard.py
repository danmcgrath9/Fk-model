"""Mercer Tipping staking card (1 Nov 2026, founder: "a card showing importance of staking"): the same posted tips
staked our way against 1u on every tip, bars that can go below zero, and the winners' stakes. whycard.py's look.
python stakecard.py STAKE.json OUT.png"""
import asyncio, glob, html, json, sys
from whycard import CSS as WHY_CSS, GOLD, PALE, LINE, RED
CSS = WHY_CSS + f"""
.zb{{display:grid;grid-template-columns:330px 1fr 170px;align-items:center;column-gap:16px;height:64px}}
.zb .k{{font:600 30px/1.1 BC;color:{PALE};letter-spacing:1px}} .zb .t{{height:42px;position:relative;border-left:3px solid {PALE}}}
.zb .f{{position:absolute;top:0;bottom:0;border-radius:4px}} .zb .v{{font:800 48px/1 BC;text-align:right;font-variant-numeric:tabular-nums}}
.tbl .wr.hd{{font:600 24px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;height:40px}}
.tbl .wr{{grid-template-columns:1fr 130px 110px 150px 150px;height:44px;font-size:31px}} .tbl.c3 .wr{{grid-template-columns:1fr 150px 150px}}
.tbl .wr .neg{{color:{RED}}} .sec{{margin-top:22px}} .sec h3{{margin-bottom:8px}} .end{{margin-top:22px;font-size:38px}} .zb{{height:56px}}
"""
def zbars(items, lo, hi):
    # zero sits at the same x on every bar: a loss runs left of it in red, a profit right of it in gold
    span = hi - lo; z = 100 * -lo / span
    out = ""
    for k, v, lab in items:
        c = GOLD if v >= 0 else RED
        w = max(1.2, 100 * abs(v) / span); left = z if v >= 0 else z - w
        out += (f"<div class='zb'><div class='k'>{html.escape(k)}</div><div class='t' style='border-left:0;background:linear-gradient(90deg,transparent calc({z:.1f}% - 1.5px),{PALE} calc({z:.1f}% - 1.5px),{PALE} calc({z:.1f}% + 1.5px),transparent calc({z:.1f}% + 1.5px))'>"
                f"<div class='f' style='left:{left:.1f}%;width:{w:.1f}%;background:{c}'></div></div><div class='v' style='color:{c}'>{html.escape(lab)}</div></div>")
    return out
def card(d):
    secs = ""
    for s in d["sections"]:
        body = zbars([(i["k"], i["v"], i["label"]) for i in s["zbars"]], s["lo"], s["hi"]) if s.get("zbars") else ""
        if s.get("table"):
            rows = ([("hd", s["head"])] if s.get("head") else []) + [("", r) for r in s["table"]]
            body += f"<div class='tbl {s.get('cls', '')}'>" + "".join(f"<div class='wr {c}'>" + "".join(f"<div class='{('neg' if x.startswith('-') else 'g' if j == s.get('gold', len(r) - 1) else '') if not c else ''}'>{html.escape(x)}</div>" for j, x in enumerate(r)) + "</div>" for c, r in rows) + "</div>"
        body += "".join(f"<div class='line'>{l}</div>" for l in s.get("lines", []))
        secs += f"<div class='sec'><h3>{html.escape(s['h'])}</h3>{body}</div>"
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>{secs}"
            f"<div class='end'>{d['end']}</div><div style='flex:1'></div>"
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
