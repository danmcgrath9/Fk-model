"""Mercer Tipping explainer card (25 Oct 2026, founder: "why it's not sustainable ROI but sustainable positive long
term"): a week's ROI against the other weeks since we started, how much rode on the biggest winners, and the price-v-BSP record,
1080x1350, tipcard.py's look.   python whycard.py WHY.json OUT.png"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
RED = "#e0645a"
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.sec{{margin-top:30px}} .sec h3{{font:800 34px/1 BC;color:{GOLD};letter-spacing:4px;text-transform:uppercase;margin-bottom:14px}}
.bars .b{{display:grid;grid-template-columns:360px 1fr 160px;align-items:center;column-gap:16px;height:54px}}
.bars .k{{font:600 30px/1.1 BC;color:{PALE};letter-spacing:1px}} .bars .t{{height:38px;position:relative}}
.bars .f{{position:absolute;left:0;top:0;bottom:0;border-radius:4px}} .bars .v{{font:800 46px/1 BC;text-align:right;font-variant-numeric:tabular-nums}}
.tbl .wr{{display:grid;grid-template-columns:1fr 150px 150px;align-items:baseline;column-gap:16px;height:52px;border-bottom:2px solid {LINE};font:600 33px/1 BC}}
.tbl .wr div:not(:first-child){{text-align:right;font-variant-numeric:tabular-nums}} .tbl .wr .g{{color:{GOLD};font-weight:800}}
.line{{font:600 33px/1.4 BC;color:{INK};letter-spacing:.5px}} .line b{{color:{GOLD};font-weight:800}}
.end{{margin-top:32px;border-top:3px solid {GOLD};padding-top:22px;font:800 42px/1.15 BC;text-transform:uppercase;letter-spacing:1px}}
.end span{{color:{GOLD}}}
"""
def bars(items, mx):
    return "".join(f"<div class='b'><div class='k'>{html.escape(k)}</div><div class='t'><div class='f' style='width:{max(1.5, 100 * v / mx):.1f}%;background:{c}'></div></div>"
                   f"<div class='v' style='color:{c}'>{html.escape(lab)}</div></div>" for k, v, lab, c in items)
def card(d):
    secs = ""
    for s in d["sections"]:
        body = bars([(i["k"], i["v"], i["label"], GOLD if i.get("hi") else PALE) for i in s["bars"]], s["max"]) if s.get("bars") else ""
        if s.get("table"):  # rows of cells, numbers right-aligned in columns (25 Oct 2026, founder: "the numbers aren't lined up")
            body += "<div class='tbl'>" + "".join("<div class='wr'>" + "".join(f"<div class='{'g' if j == len(r) - 1 else ''}'>{html.escape(c)}</div>" for j, c in enumerate(r)) + "</div>" for r in s["table"]) + "</div>"
        body += "".join(f"<div class='line'>{l}</div>" for l in s.get("lines", []))
        secs += f"<div class='sec'><h3>{html.escape(s['h'])}</h3><div class='bars'>{body}</div></div>"
    return (f"<html><head><style>{CSS}</style></head><body>"
            f"<div class='top'><div class='lock'><div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div></div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>{secs}"
            f"<div class='end'>{d['end']}</div><div style='flex:1'></div>"
            f"<div class='foot'><span></span><span>18+ · Gamble responsibly</span></div></body></html>")
async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()
if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
