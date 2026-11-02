"""Paper lay sheet for a race day (rule fixed 23 Oct 2026, data/live_bets/betmatic-book.md "Paper lay book"):
lay at Betfair SP if BSP is $15-$40 AND at least 1.6x our price (band widened $30 -> $40 on 28 Oct 2026, before the
first race; this script still said $30 until 2 Nov). Our price = the live shaded model (p_model: stage 2,
back-settler shade, before the blend with the open). First starters and runners with no Australian form held
(internationals) are excluded. Only runners whose trigger is $40 or under can qualify (ours $25 or shorter).
python lay_sheet.py DAYPREFIX GTAG NPZ [--html PAGE.html]  (prints one CSV row per runner with a trigger; --html also
writes the list as a "Lay book" section at the bottom of the meeting page, 2 Nov 2026, founder: "why aren't the lay bets
just part of this artifact always down the bottom?")"""
import html, json, os, re, sys, numpy as np
L = "/home/user/fk-model/data/live_bets"; pre, g, npz = sys.argv[1:4]
page = sys.argv[sys.argv.index("--html") + 1] if "--html" in sys.argv else None
LAY_MIN, LAY_MAX, LAY_X = 15.0, 40.0, 1.6
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
rows = json.load(open(f"{L}/{pre}-{g}-v6.json")); fs = json.load(open(f"{L}/{pre}-{g}-first-starters.json"))
fsk = {norm(x.split("|")[-1]) if isinstance(x, str) else norm(str(x)) for x in (fs if isinstance(fs, list) else fs.keys())}
px = {}
for l in open(f"{L}/{pre}-prices.txt"):
    pa = [x.strip() for x in l.split("#")[0].split(",")]
    if len(pa) >= 3 and pa[0].isdigit() and pa[2].upper() != "SCR": px[(int(pa[0]), norm(pa[1]))] = pa[2]
U = np.load(npz, allow_pickle=True); c = list(U["cols"]); f = {str(x): i for i, x in enumerate(U["past_fields"])}
held = {norm(str(n)): bool(np.isfinite(U["P"][i, :, f["finish"]]).any()) for i, n in enumerate(U["name"])}
starts = {norm(str(n)): float(np.nan_to_num(U["X"][i, c.index("f_careerForm_s")], nan=0)) for i, n in enumerate(U["name"])} if "f_careerForm_s" in c else {}
by = {}
for r in rows: by.setdefault(r["race_id"], []).append(r)
nums = {}
if os.path.exists(f"{L}/{pre}-entry-numbers.txt"):
    for l in open(f"{L}/{pre}-entry-numbers.txt"):
        pa = l.strip().split("|")
        if len(pa) == 5 and pa[0].isdigit(): nums[(int(pa[0]), norm(pa[2]))] = pa[1]
print("race,horse,ours,lay_if_bsp_at_least,lay_if_bsp_at_most,price_now,note")
out = []
for rid, rs in sorted(by.items(), key=lambda t: t[1][0]["race"]):
    s = sum(r["p_model"] for r in rs)
    for r in sorted(rs, key=lambda r: -r["p_model"]):
        ours = s / r["p_model"]; trig = max(LAY_MIN, LAY_X * ours)
        if trig > LAY_MAX: continue
        k = norm(r["horse"]); note = ""
        if k in fsk: note = "first starter: excluded"
        elif not held.get(k, True): note = "no Australian form held (international): excluded"
        now = px.get((r["race"], k), "")
        print(f'{r["race"]},{r["horse"]},{ours:.2f},{trig:.2f},{LAY_MAX:g},{now},{note}')
        if not note:
            out.append((r["race"], nums.get((r["race"], k), ""), r["horse"], ours, trig, now))
if page:
    START, END = "<!-- lays -->", "<!-- /lays -->"
    trs = "".join(f"<tr><td><a href='#r{rc}'>R{rc}</a></td><td>{n}</td><td>{html.escape(h)}</td><td>${o:.2f}</td>"
                  f"<td>${t:.2f} to ${LAY_MAX:.0f}</td><td>{'$' + now if now and now != '0' else '-'}</td></tr>"
                  for rc, n, h, o, t, now in out)
    sec = (f"{START}<h2>Lay book ({len(out)})</h2><div>Paper. Lay 1u at Betfair SP when the SP lands in the range: "
           f"at least ${LAY_MIN:.0f} and at least {LAY_X:g}x our price, up to ${LAY_MAX:.0f}.</div><div class='tw'><table>"
           f"<tr><th>Race</th><th>No.</th><th>Horse</th><th>Our price</th><th>Lay if Betfair SP is</th><th>Price now</th></tr>"
           f"{trs}</table></div>{END}") if out else f"{START}<h2>Lay book (0)</h2><div>None.</div>{END}"
    pg = open(page).read()
    pg = re.sub(re.escape(START) + ".*?" + re.escape(END), "", pg, flags=re.S)
    i = pg.rfind("</body>")
    pg = pg[:i] + sec + pg[i:] if i >= 0 else pg + sec
    open(page, "w").write(pg)
    print(f"{page}: lay book, {len(out)} runners", file=sys.stderr)
