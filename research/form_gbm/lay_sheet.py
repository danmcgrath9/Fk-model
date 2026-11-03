"""Paper lay sheet for a race day (rule fixed 23 Oct 2026, data/live_bets/betmatic-book.md "Paper lay book"):
lay at Betfair SP if BSP is $15-$40 AND at least 1.6x our price (band widened $30 -> $40 on 28 Oct 2026, before the
first race; this script still said $30 until 2 Nov). Our price = the live shaded model (p_model: stage 2,
back-settler shade, before the blend with the open). First starters and runners with no Australian form held
(internationals) are excluded. Only runners whose trigger is $40 or under can qualify (ours $25 or shorter).
python lay_sheet.py DAYPREFIX GTAG NPZ [--html PAGE.html]  (prints one CSV row per runner with a trigger; --html also
writes the list as a "Lay book" section at the bottom of the meeting page, 2 Nov 2026, founder: "why aren't the lay bets
just part of this artifact always down the bottom?")
3 Nov 2026 (founder: "a lay and back table down the bottom ... a game day tab, where I can go to the race and see what we
are laying and potentially back in at bsp"): the same run also lists the BACK candidates (t_fav47_months.py,
t_fav47_live.py: back the Betfair SP FAVOURITE at $4-$7 when we rate it 1.6x the BSP or longer, flat 1u, paper), writes
them to DAYPREFIX-GTAG-backs.csv, puts a back table under the lay table, and a "Game day" section race by race with the
lays and the backs for that race, reached from a Game day button in the top bar."""
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
BACK_LO, BACK_HI, BACK_X = 4.0, 7.0, 1.6
backs = []   # (race, number, horse, ours, back_up_to, now): back at SP only if it is the favourite and its BSP is $4 to back_up_to
for rid, rs in sorted(by.items(), key=lambda t: t[1][0]["race"]):
    s_ = sum(r["p_model"] for r in rs)
    for r in sorted(rs, key=lambda r: -r["p_model"]):
        ours = s_ / r["p_model"]; cap = min(BACK_HI, ours / BACK_X); k = norm(r["horse"])
        if cap < BACK_LO or k in fsk or not held.get(k, True): continue
        backs.append((r["race"], nums.get((r["race"], k), ""), r["horse"], ours, cap, px.get((r["race"], k), "")))
with open(f"{L}/{pre}-{g}-backs.csv", "w") as fh:
    fh.write("race,horse,ours,back_if_favourite_bsp_at_least,back_if_favourite_bsp_at_most,price_now\n")
    for rc, n, h, o, cap, now in backs: fh.write(f"{rc},{h},{o:.2f},{BACK_LO:.2f},{cap:.2f},{now}\n")
if page:
    # Every runner the rule names, in one table grouped by race, nothing added to the rule (founder, 2 Nov 2026: "its not
    # even our rules, just make it all a bit pretty table"). Columns: number, horse, our price, the Betfair SP range it is
    # a lay in, and the bookies' price now.
    START, END = "<!-- lays -->", "<!-- /lays -->"
    def money(x):
        return f"${x:.0f}" if abs(x - round(x)) < 0.005 else f"${x:.2f}"
    def pnow(x):
        try: return float(x) or None
        except (TypeError, ValueError): return None
    trs, last, k = [], None, 0
    for rc, n, h, o, t, now in out:
        x = pnow(now)
        if rc != last:
            cnt = sum(1 for r in out if r[0] == rc)
            trs.append(f"<tr class='rh'><td colspan='5'><a href='#r{rc}'>Race {rc}</a> <span>{cnt} runners</span></td></tr>")
            last, k = rc, 0
        k += 1
        trs.append(f"<tr class='{'z' if k % 2 == 0 else ''}'><td class='cn'>{n}</td><td class='hn'>{html.escape(h)}</td>"
                   f"<td>{money(o)}</td><td class='lay'>{money(t)}+</td><td>{money(x) if x else '-'}</td></tr>")
    css = ("<style>.lb{border:2px solid #6a1b9a;border-radius:10px;padding:12px 12px 6px;margin:22px 0}"
           ".lb h2{margin:0 0 4px;border:0;padding:0;font-size:18px}.lb .rule{font-size:13px;color:#555;margin-bottom:8px}"
           ".lb table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}"
           ".lb th{font-size:11.5px;color:#666;font-weight:600;text-transform:uppercase;letter-spacing:.04em;padding:6px;"
           "text-align:right;border-bottom:1px solid #ddd;padding:6px 4px}.lb th:nth-child(-n+2){text-align:left}"
           ".lb td{padding:7px 4px;text-align:right;border-bottom:1px solid #eee}.lb td.cn{text-align:left;color:#777;width:24px}"
           ".lb td.hn{text-align:left;font-weight:600;overflow-wrap:anywhere}.lb td.lay{font-weight:700;color:#6a1b9a;white-space:nowrap}"
           ".lb tr.z td{background:#faf7fc}.lb tr.rh td{text-align:left;background:#6a1b9a;color:#fff;font-weight:700;"
           "padding:6px 8px;border:0}.lb tr.rh a{color:#fff;text-decoration:none}.lb tr.rh span{font-weight:400;opacity:.85;"
           "margin-left:6px;font-size:12.5px}@media(prefers-color-scheme:dark){.lb{border-color:#ba68c8}.lb .rule,.lb th{color:#aaa}"
           ".lb td{border-color:#333}.lb tr.z td{background:#1e1a22}.lb td.lay{color:#ce93d8}.lb tr.rh td{background:#4a148c}}"
           ".lb.bb{border-color:#1b5e20}.lb.bb td.lay{color:#1b5e20}.lb.bb tr.rh td{background:#1b5e20}.lb.bb tr.z td{background:#f4faf4}"
           ".lb.gd{border-color:#37474f}.lb.gd h3{margin:14px 0 4px;font-size:15px}.lb.gd h3 a{color:inherit;text-decoration:none}"
           ".lb.gd h3 span{font-weight:400;color:#777;font-size:12.5px;margin-left:6px}.lb.gd td.bk{font-weight:700;color:#1b5e20;white-space:nowrap}"
           ".lb.gd th:nth-child(-n+3){text-align:left}.lb.gd td:nth-child(3){text-align:left;font-size:12px;color:#555}"
           "@media(prefers-color-scheme:dark){.lb.bb{border-color:#66bb6a}.lb.bb td.lay{color:#81c784}.lb.bb tr.rh td{background:#1b5e20}"
           ".lb.bb tr.z td{background:#1a221a}.lb.gd td.bk{color:#81c784}.lb.gd td:nth-child(3){color:#aaa}}</style>")
    # the back table: same shape as the lay table, green, under it
    # on the page only the runners that could be the favourite: a bookies' price now of $10 or under (every candidate is in the
    # CSV, because any runner can end up favourite at the jump), shortest first
    shown = sorted([b for b in backs if (pnow(b[5]) <= 10 if pnow(b[5]) else b[3] <= 12)], key=lambda b: (b[0], pnow(b[5]) or b[3]))   # no market yet: our own $12 and under
    btrs, last, k = [], None, 0
    for rc, n, h, o, cap, now in shown:
        x = pnow(now)
        if rc != last:
            cnt = sum(1 for r in shown if r[0] == rc)
            btrs.append(f"<tr class='rh'><td colspan='5'><a href='#r{rc}'>Race {rc}</a> <span>{cnt} runners</span></td></tr>")
            last, k = rc, 0
        k += 1
        btrs.append(f"<tr class='{'z' if k % 2 == 0 else ''}'><td class='cn'>{n}</td><td class='hn'>{html.escape(h)}</td>"
                    f"<td>{money(o)}</td><td class='lay'>$4 to {money(cap)}</td><td>{money(x) if x else '-'}</td></tr>")
    back_sec = (f"<div class='lb bb' id='backs' style='scroll-margin-top:64px'><h2>Back book: {len(shown)} runners</h2>"
                f"<div class='rule'>Paper, 1u at Betfair SP. Back a horse only if it is the <b>favourite</b> at the jump and its Betfair SP "
                f"is $4 to its <b>back if fav</b> price (that is our price divided by 1.6, capped at $7). Backtest +79% on 61 bets, "
                f"the live weeks 6 from 17.</div>"
                f"<div class='tw'><table><tr><th>No.</th><th>Horse</th><th>Ours</th><th>Back if fav</th><th>Now</th></tr>"
                f"{''.join(btrs)}</table></div></div>") if shown else "<div class='lb bb' id='backs'><h2>Back book: none</h2></div>"
    # game day: one block per race with that race's lays and backs, the thing to read in the last two minutes
    races = sorted({r[0] for r in out} | {r[0] for r in shown})
    gd = []
    for rc in races:
        ls = [r for r in out if r[0] == rc]; bs_ = [r for r in shown if r[0] == rc]
        rows_ = []
        for _, n, h, o, t, now in ls:
            x = pnow(now)
            rows_.append(f"<tr><td class='cn'>{n}</td><td class='hn'>{html.escape(h)}</td><td>LAY</td><td class='lay'>{money(t)}+</td><td>{money(x) if x else '-'}</td></tr>")
        for _, n, h, o, cap, now in bs_:
            x = pnow(now)
            rows_.append(f"<tr><td class='cn'>{n}</td><td class='hn'>{html.escape(h)}</td><td>BACK fav</td><td class='bk'>$4 to {money(cap)}</td><td>{money(x) if x else '-'}</td></tr>")
        gd.append(f"<div class='gdr'><h3><a href='#r{rc}'>Race {rc}</a> <span>{len(ls)} lays, {len(bs_)} backs</span></h3>"
                  f"<div class='tw'><table><tr><th>No.</th><th>Horse</th><th>Side</th><th>SP</th><th>Now</th></tr>{''.join(rows_)}</table></div></div>")
    gd_sec = (f"<div class='lb gd' id='gameday' style='scroll-margin-top:64px'><h2>Game day</h2>"
              f"<div class='rule'>Race by race, in the last two minutes: a LAY goes on at Betfair SP (max $40) if the projected SP is at or over "
              f"its price; a BACK goes on at Betfair SP only if the horse is the favourite and the projected SP is inside its range. "
              f"Under the price, or not the favourite: nothing.</div>{''.join(gd)}</div>") if races else "<div class='lb gd' id='gameday'><h2>Game day: nothing to do</h2></div>"
    sec = (f"{START}{css}<div class='lb' id='lays' style='scroll-margin-top:64px'><h2>Lay book: {len(out)} runners</h2>"
           f"<div class='rule'>Paper, 1u = $200 laid at Betfair SP. Lay a horse if its Betfair SP finishes at its <b>lay if SP</b> "
           f"price or higher, up to ${LAY_MAX:.0f}. That price is $15, or 1.6x our price if higher. Now is the bookies' price.</div>"
           f"<div class='tw'><table><tr><th>No.</th><th>Horse</th><th>Ours</th><th>Lay if SP</th><th>Now</th></tr>"
           f"{''.join(trs)}</table></div></div>") if out else "<div class='lb' id='lays'><h2>Lay book: none</h2></div>"
    sec = f"{START}{css}{gd_sec}{sec}{back_sec}{END}"
    pg = open(page).read()
    pg = re.sub(re.escape(START) + ".*?" + re.escape(END), "", pg, flags=re.S)
    # a "Lays" button beside Bets at the start of the page's top bar (on a phone the end of the bar is off screen), so the book is one tap away (founder, 2 Nov 2026)
    if "href='#lays'" not in pg and "Bets</a>" in pg:
        pg = pg.replace("Bets</a>", "Bets</a><a href='#lays' style='background:#6a1b9a;color:#fff'>Lays</a>", 1)
    if "href='#gameday'" not in pg and "Lays</a>" in pg:
        pg = pg.replace("Lays</a>", "Lays</a><a href='#gameday' style='background:#37474f;color:#fff'>Game day</a>", 1)
    i = pg.rfind("</body>")
    pg = pg[:i] + sec + pg[i:] if i >= 0 else pg + sec
    open(page, "w").write(pg)
    print(f"{page}: lay book {len(out)} runners, back book {len(shown)} shown of {len(backs)} candidates, game day {len(races)} races", file=sys.stderr)
