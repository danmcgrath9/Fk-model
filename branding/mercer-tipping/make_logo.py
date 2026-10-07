"""Mercer Tipping profile pictures: simple type marks, 800x800, rendered with Chromium."""
import asyncio, glob, base64
from playwright.async_api import async_playwright
f=lambda n: base64.b64encode(open(n,'rb').read()).decode()
FONTS=f"""@font-face{{font-family:BC;font-weight:800;src:url(data:font/woff2;base64,{f('BarlowCondensed-800.woff2')}) format('woff2')}}
@font-face{{font-family:BC;font-weight:600;src:url(data:font/woff2;base64,{f('BarlowCondensed-600.woff2')}) format('woff2')}}
@font-face{{font-family:LB;font-weight:700;src:url(data:font/woff2;base64,{f('LibreBaskerville-700.woff2')}) format('woff2')}}"""
def word(bg,fg,acc):   # MERCER over a rule, TIPPING spaced underneath
    return f"""<div class='c' style='background:{bg}'><div>
<div style='font:800 196px/0.9 BC;color:{fg};letter-spacing:4px'>MERCER</div>
<div style='height:6px;background:{acc};margin:26px auto 24px;width:300px'></div>
<div style='font:600 64px/1 BC;color:{acc};letter-spacing:22px;padding-left:22px'>TIPPING</div></div></div>"""
def mono(bg,fg,acc):   # serif M with TIPPING underneath
    return f"""<div class='c' style='background:{bg}'><div>
<div style='font:700 420px/0.85 LB;color:{fg}'>M</div>
<div style='font:600 60px/1 BC;color:{acc};letter-spacing:20px;padding-left:20px;margin-top:34px'>MERCER TIPPING</div></div></div>"""
V={"mercer-tipping-navy":word("#13233a","#ffffff","#e0b04a"),
   "mercer-tipping-green":word("#17402c","#ffffff","#e0b04a"),
   "mercer-tipping-monogram":mono("#13233a","#ffffff","#e0b04a")}
PAGE="<html><head><style>{fonts}body{{margin:0}}.c{{width:800px;height:800px;display:flex;align-items:center;justify-content:center;text-align:center}}</style></head><body>{body}</body></html>"
async def main():
    exe=glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")[0]
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=exe); pg=await b.new_page(viewport={"width":800,"height":800})
        for n,h in V.items():
            await pg.set_content(PAGE.format(fonts=FONTS,body=h)); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f"{n}.png")
        await pg.set_viewport_size({"width":960,"height":330})
        imgs="".join(f"<div style='text-align:center;font:14px sans-serif'><img src='file://{__import__('os').getcwd()}/{n}.png' style='width:250px;height:250px;border-radius:50%;display:block;margin:0 auto 8px'>{n}</div>" for n in V)
        await pg.goto("about:blank"); await pg.set_content(f"<html><body style='margin:0;display:flex;gap:40px;justify-content:center;align-items:center;height:330px;background:#fff'>{imgs}</body></html>")
        await pg.wait_for_timeout(300); await pg.screenshot(path="preview-circle.png"); await b.close()
asyncio.run(main()); print("ok")
