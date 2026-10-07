"""Dan Mercer profile pictures: racing silks, rendered to PNG with Chromium."""
import asyncio, glob
from playwright.async_api import async_playwright

JACKET = "M 330 318 L 400 368 L 470 318 L 562 338 L 658 470 L 606 520 L 538 432 L 544 640 L 256 640 L 262 432 L 194 520 L 142 470 L 238 338 Z"
CAP = ("<path d='M 318 262 Q 318 168 400 168 Q 482 168 482 262 Z' fill='{cap}'/>"
       "<path d='M 300 262 L 500 262 Q 520 262 520 276 L 520 280 L 300 280 Z' fill='{peak}'/>"
       "<circle cx='400' cy='172' r='9' fill='{peak}'/>")

def silks(bg, jacket, trim, cap, peak, pattern, size=800):
    pat = {
        "sash": f"<polygon points='190,330 290,330 610,700 510,700' fill='{trim}' clip-path='url(#j)'/>",
        "hoops": "".join(f"<rect x='100' y='{y}' width='600' height='34' fill='{trim}' clip-path='url(#j)'/>" for y in (420, 500, 580)),
        "cross": f"<polygon points='240,330 300,330 560,640 500,640' fill='{trim}' clip-path='url(#j)'/><polygon points='560,330 500,330 240,640 300,640' fill='{trim}' clip-path='url(#j)'/>",
    }[pattern]
    return f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 800' width='{size}' height='{size}'>
<rect width='800' height='800' fill='{bg}'/>
<defs><clipPath id='j'><path d='{JACKET}'/></clipPath></defs>
<g transform='translate(400,415) scale(1.18) translate(-400,-405)'>
<path d='{JACKET}' fill='{jacket}'/>{pat}
<path d='M 330 318 L 400 368 L 470 318' fill='none' stroke='{trim}' stroke-width='10' stroke-linejoin='round'/>
<rect x='196' y='496' width='0' height='0'/>
{CAP.format(cap=cap, peak=peak)}
</g></svg>"""

VARIANTS = {
    "dan-mercer-navy-gold-sash": silks("#f2ede3", "#1b2f4b", "#d9a93b", "#d9a93b", "#1b2f4b", "sash"),
    "dan-mercer-green-white-hoops": silks("#f2ede3", "#1f5a3c", "#ffffff", "#1f5a3c", "#ffffff", "hoops"),
    "dan-mercer-navy-on-navy": silks("#16263d", "#f2ede3", "#c8102e", "#c8102e", "#f2ede3", "sash"),
}

async def main():
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=exe)
        pg = await b.new_page(viewport={"width": 800, "height": 800})
        for name, svg in VARIANTS.items():
            open(f"{name}.svg", "w").write(svg)
            await pg.set_content(f"<html><body style='margin:0'>{svg}</body></html>")
            await pg.screenshot(path=f"{name}.png", clip={"x": 0, "y": 0, "width": 800, "height": 800})
        # preview: all three as Twitter would crop them (circle), side by side
        small = {n: svg.replace("width='{0}' height='{0}'".format(800), "width='240' height='240'", 1) for n, svg in VARIANTS.items()}
        label = {n: n.replace("dan-mercer-", "").replace("-", " ") for n in VARIANTS}
        imgs = "".join(f"<div style='text-align:center;font:14px sans-serif'><div style='width:240px;height:240px;border-radius:50%;overflow:hidden;margin:0 auto 8px'>{small[n]}</div>{label[n]}</div>" for n in VARIANTS)
        await pg.set_viewport_size({"width": 900, "height": 320})
        await pg.set_content(f"<html><body style='margin:0;background:#fff;display:flex;gap:40px;justify-content:center;align-items:center;height:320px'>{imgs}</body></html>")
        await pg.screenshot(path="preview-circle-crop.png")
        await b.close()
asyncio.run(main())
print("ok")
