"""World Pool days against other tote days, bookie SP and Betfair SP (26 Oct 2026, founder: "find out all the world pool
days. Compare it to actual other tote days / and then bookie starting price and Betfair sp"). DB only, no credits.

Source: every stored past run (entries' raw pastEvents: date, track, finish, benchmark sp / bsp / bestToteWin). The tote
is bestToteWin (best of the three TAB totes); on a World Pool race the Australian TAB pool is commingled into the HKJC
pool (unverified here), so the TAB tote there should be the World Pool price. Days are from HKJC / TDN / news reports
(26 Oct 2026 web search); CONFIRMED = named in a report as a World Pool day; LIKELY = the same carnival day in a year
we found no report for. On some days only some races were commingled (2025 Everest day two races, 2025 Caulfield Cup
day the Cup only), so a day-level label overstates World Pool coverage on those days.
The returns in this sample run high (past runs of horses still racing); read across rows (same runs, different price
source), and compare groups on the ratios, not on the ROI level.
    python scripts/world_pool_tote.py"""
from __future__ import annotations
import os, re, collections, datetime as dt, statistics as st
from zoneinfo import ZoneInfo
import psycopg

C, L = "confirmed", "likely"
WP = {  # (date, track keyword) -> label
    ("2023-02-18", "flemington"): (C, "Lightning Stakes Day"), ("2023-10-07", "flemington"): (C, "Turnbull Stakes Day"),
    ("2023-10-14", "randwick"): (C, "The Everest Day"), ("2023-10-21", "caulfield"): (C, "Caulfield Cup Day"),
    ("2023-10-28", "moonee valley"): (C, "Cox Plate Day"), ("2023-11-04", "flemington"): (C, "Victoria Derby Day"),
    ("2024-02-24", "caulfield"): (C, "Blue Diamond Day"), ("2024-03-30", "flemington"): (C, "Australian Cup Day"),
    ("2024-03-30", "rosehill"): (C, "Tancred Stakes Day"), ("2024-04-06", "randwick"): (C, "Doncaster Mile Day"),
    ("2024-04-13", "randwick"): (C, "Queen Elizabeth Stakes Day"),
    ("2024-02-17", "flemington"): (L, "Lightning Stakes Day"), ("2024-06-08", "eagle farm"): (L, "Stradbroke Day"),
    ("2024-10-19", "randwick"): (L, "The Everest Day"), ("2024-10-19", "caulfield"): (L, "Caulfield Cup Day"),
    ("2024-10-26", "moonee valley"): (L, "Cox Plate Day"), ("2024-11-02", "flemington"): (L, "Victoria Derby Day"),
    ("2025-04-05", "randwick"): (L, "Doncaster Mile Day"), ("2025-04-12", "randwick"): (L, "Queen Elizabeth Stakes Day"),
    ("2025-05-03", "morphettville"): (C, "SA Derby Day"), ("2025-05-17", "doomben"): (C, "Doomben 10000 Day"),
    ("2025-05-24", "doomben"): (C, "Doomben Cup Day"), ("2025-06-07", "eagle farm"): (L, "Stradbroke Day"),
    ("2025-10-18", "randwick"): (C, "The Everest Day (2 races)"), ("2025-10-18", "caulfield"): (C, "Caulfield Cup Day (Cup only)"),
    ("2025-10-25", "moonee valley"): (C, "Cox Plate Day"), ("2025-11-01", "flemington"): (C, "Victoria Derby Day"),
    ("2026-02-28", "flemington"): (C, "Australian Guineas Day"), ("2026-02-28", "randwick"): (C, "Chipping Norton Day"),
    ("2026-03-21", "rosehill"): (C, "Golden Slipper Day"), ("2026-04-18", "randwick"): (L, "All Aged Stakes Day"),
    ("2026-08-22", "randwick"): (C, "Winx Stakes Day"), ("2026-08-29", "caulfield"): (C, "Memsie Stakes Day"),
    ("2026-09-19", "caulfield"): (C, "Sir Rupert Clarke Day"), ("2026-10-03", "flemington"): (C, "Turnbull Stakes Day"),
    ("2026-10-10", "randwick"): (L, "The Everest Day"), ("2026-10-17", "caulfield"): (L, "Caulfield Cup Day"),
    ("2026-10-24", "flemington"): (L, "Cox Plate Day (at Flemington)"),
}
METRO = ("flemington", "caulfield", "moonee valley", "randwick", "rosehill", "eagle farm", "doomben", "morphettville", "sandown")
q = """select p->>'raceId', coalesce(p->'horse'->>'id', e.horse_id::text), p->>'date', coalesce(p->'track'->>'name', p->>'track'),
          p->>'state', (p->>'finishPosition')::int, (p->'benchmark'->>'sp')::numeric, (p->'benchmark'->>'bsp')::numeric,
          (p->'benchmark'->>'bestToteWin')::numeric, coalesce((p->>'trial')::boolean, false)
       from fk.entries e, jsonb_array_elements(coalesce(e.raw->'pastEvents', '[]'::jsonb)) p where p ? 'benchmark'"""
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute(q).fetchall()
mel = ZoneInfo("Australia/Melbourne")
def day(d):
    if d is None: return ""
    if re.fullmatch(r"\d+(\.\d+)?", str(d)):
        v = float(d); v = v / 1000 if v > 1e11 else v   # seconds or milliseconds
        return dt.datetime.fromtimestamp(v, mel).date().isoformat()
    return str(d)[:10]
seen, R = set(), []
for rid, hid, d, trk, stt, fin, sp, bsp, tote, trial in rows:
    if trial or not rid or fin is None or not sp or not bsp or not tote or (rid, hid) in seen: continue
    seen.add((rid, hid)); t = (trk or "").lower(); D = day(d)
    lab = next((v for (dd, kw), v in WP.items() if dd == D and kw in t), None)
    wd = dt.date.fromisoformat(D).weekday() if D else -1
    grp = ("World Pool (" + lab[0] + ")") if lab else ("Other metro Saturday" if wd == 5 and any(m in t for m in METRO) else "All other meetings")
    R.append(dict(race=rid, date=D, track=trk, state=stt, fin=fin, sp=float(sp), bsp=float(bsp), tote=float(tote), grp=grp, wp=lab[1] if lab else None))
R = [x for x in R if x["sp"] > 1 and x["bsp"] > 1 and x["tote"] > 1]
print(f"{len(R)} unique past runs with SP, BSP and tote; dates {min(x['date'] for x in R)} to {max(x['date'] for x in R)}")
med = lambda v: st.median(v) if v else float("nan")
def row(xs, lab):
    w = [x for x in xs if x["fin"] == 1]
    roi = lambda k, cm=0: 100 * sum(((x[k] - 1) * (1 - cm)) if x["fin"] == 1 else -1 for x in xs) / len(xs)
    print(f"| {lab} | {len(xs)} | {len(w)} | {med([x['tote']/x['sp'] for x in xs]):.3f} | {med([x['bsp']/x['sp'] for x in xs]):.3f} | "
          f"{med([x['tote']/x['bsp'] for x in xs]):.3f} | {roi('sp'):+.1f}% | {roi('tote'):+.1f}% | {roi('bsp', .08):+.1f}% |")
H = "| group | runs | winners | tote/SP | BSP/SP | tote/BSP | ROI SP | ROI tote | ROI BSP net 8% |\n|---|---|---|---|---|---|---|---|---|"
groups = ["World Pool (confirmed)", "World Pool (likely)", "Other metro Saturday", "All other meetings"]
print("\n## All prices\n" + H)
for g in groups:
    xs = [x for x in R if x["grp"] == g]
    if xs: row(xs, g)
for lo, hi, nm in ((1, 5, "SP under $5"), (5, 13, "SP $5-$13"), (13, 1e9, "SP $13 and over")):
    print(f"\n## {nm}\n" + H)
    for g in groups:
        xs = [x for x in R if x["grp"] == g and lo <= x["sp"] < hi]
        if xs: row(xs, g)
print("\n## World Pool days found in the data")
c = collections.Counter((x["date"], x["wp"], x["grp"]) for x in R if x["wp"])
for (d, w, g), n in sorted(c.items()): print(f"{d} {w} [{g.split('(')[1][:-1]}]: {n} runs")
missing = [f"{d} {v[1]}" for (d, k), v in WP.items() if not any(x["date"] == d and x["wp"] == v[1] for x in R)]
print("\nWorld Pool days with no runs in our data:", "; ".join(missing))
