"""Mercer Tipping ratings chart (8 Nov 2026, founder: "Give me a chart and put Cavill avenue on there with an 85ish"):
one row per horse, Form King's weight-for-age rating, last start as a filled dot, best of its recent runs as a ring,
a marked horse in white. 1080x1350, tipcard.py's look.
python ratingcard.py RATINGS.json OUT.png
RATINGS.json: {"title", "sub", "lo", "hi", "rows": [{"horse", "last", "best", "line", "mark"}]}"""
import asyncio, glob, html, json, sys
from tipcard import CSS as TIP_CSS, NAVY, INK, GOLD, PALE, LINE
CSS = TIP_CSS.replace("{hs}", "40") + f"""
.key{{display:flex;gap:40px;font:600 24px/1 BC;color:{PALE};letter-spacing:3px;text-transform:uppercase;margin:46px 0 8px}}
.key i{{display:inline-block;width:22px;height:22px;border-radius:50%;margin-right:12px;vertical-align:-4px}}
svg text{{font-family:BC}}
"""
def chart(d, W=936, H=900):
    rows, lo, hi = d["rows"], d["lo"], d["hi"]
    L, R, T, B = 480, 150, 20, 56
    rh = (H - T - B) / len(rows)
    x = lambda v: L + (v - lo) / (hi - lo) * (W - L - R)
    g = []
    v = lo
    while v <= hi:
        g.append(f"<line x1='{x(v):.1f}' x2='{x(v):.1f}' y1='{T}' y2='{H-B}' stroke='{LINE}' stroke-width='2'/>"
                 f"<text x='{x(v):.1f}' y='{H-B+38}' text-anchor='middle' font-size='26' font-weight='600' fill='{PALE}'>{v:g}</text>"); v += 5
    for i, r in enumerate(rows):
        cy = T + rh * (i + 0.5); col = INK if r.get("mark") else GOLD
        g.append(f"<line x1='{L-20}' x2='{W-R+40}' y1='{T + rh*(i+1):.1f}' y2='{T + rh*(i+1):.1f}' stroke='{LINE}' stroke-width='1'/>" if i < len(rows) - 1 else "")
        g.append(f"<text x='0' y='{cy-4:.1f}' font-size='38' font-weight='800' fill='{INK}'>{html.escape(r['horse'].upper())}</text>"
                 f"<text x='0' y='{cy+30:.1f}' font-size='22' font-weight='600' fill='{PALE}' letter-spacing='1'>{html.escape(r.get('line', ''))}</text>")
        b, l_ = r.get("best"), r["last"]
        if b is not None and abs(b - l_) >= 0.3:
            g.append(f"<line x1='{x(min(b, l_)):.1f}' x2='{x(max(b, l_)):.1f}' y1='{cy:.1f}' y2='{cy:.1f}' stroke='{col}' stroke-opacity='0.45' stroke-width='4'/>"
                     f"<circle cx='{x(b):.1f}' cy='{cy:.1f}' r='13' fill='{NAVY}' stroke='{col}' stroke-width='4'/>")
        g.append(f"<circle cx='{x(l_):.1f}' cy='{cy:.1f}' r='15' fill='{col}'/>"
                 f"<text x='{x(max(l_, b or l_)) + 26:.1f}' y='{cy+11:.1f}' font-size='32' font-weight='800' fill='{col}'>{r.get('label', format(l_, '.1f'))}"
                 + (f"<tspan font-size='22' font-weight='600' fill='{PALE}' dx='8'>{r.get('sub') or 'best ' + format(b, '.1f')}</tspan>" if b is not None and abs(b - l_) >= 0.3 else "") + "</text>")
    return f"<svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(g)}</svg>"
def card(d):
    # "brand": false drops the Mercer mark and the footer, as tipcard.py's plain cards do (8 Nov 2026, founder: "Get rid of Mercer")
    brand = d.get("brand", True)
    key = (f"<div class='key'><span><i style='background:{GOLD}'></i>Last start</span>"
           f"<span><i style='border:4px solid {GOLD};box-sizing:border-box'></i>Best recent run</span></div>")
    lock = "<div class='mark'><span>M</span></div><div class='brand'>MERCER<span>TIPPING</span></div>" if brand else ""
    extra = "" if brand else ".top{justify-content:flex-start}.when{text-align:left}"
    foot = (f"<div class='foot'><span>{html.escape(d.get('foot', ''))}</span><span>18+ · Gamble responsibly</span></div>" if brand else "")
    return (f"<html><head><style>{CSS}{extra}</style></head><body>"
            f"<div class='top'><div class='lock'>{lock}</div>"
            f"<div class='when'>{html.escape(d['title'])}<span>{html.escape(d['sub'])}</span></div></div>"
            f"{key}{chart(d)}<div style='flex:1'></div>{foot}</body></html>")
async def main(src, out):
    from playwright.async_api import async_playwright
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe); pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.set_content(card(json.load(open(src)))); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out); await b.close()
if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2])); print("ok", sys.argv[2])
