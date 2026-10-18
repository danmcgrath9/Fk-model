"""Report on an odds watch (fk-odds-watch.yml): for one meeting, every stored pull of Form King's odds, race by race.
DB only, no credits.

    python scripts/odds_watch.py 2026-10-21 Kyneton

Per race: when the market opened (the first fluc), and at each pull how many runners were priced, how many bookmakers
held each runner's best price (a proxy for how many have opened and matched it), the share of runners where TAB held
the best price, and the best and average price against the open. Then the AVERAGE price from the flucs at fixed minutes
after the open (the minute-level path between pulls), and the bookmakers in the order they first appeared."""
import os, sys, statistics as st, collections
from datetime import datetime, timezone, timedelta
import psycopg
MEL = timezone(timedelta(hours=11))
day, track = sys.argv[1], sys.argv[2]
mid = f"{track.lower().replace(' ', '-')}-{day.replace('-', '')}"
fmt = lambda t: t.astimezone(MEL).strftime("%a %H:%M") if t else "?"
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute("""select r.race_number, s.horse_id, s.fetched_at, s.raw from fk.odds_snapshots s
                        join fk.races r using (race_id) where r.meeting_id = %s and s.kind = 'current'
                        order by r.race_number, s.fetched_at""", (mid,)).fetchall()
if not rows:
    sys.exit(f"no odds snapshots stored for {mid}")
print(f"# Odds watch: {track} {day}\n")
by_race = collections.defaultdict(lambda: collections.defaultdict(dict))   # race -> pull time -> horse -> raw
for rn, hid, at, raw in rows:
    by_race[rn][at.replace(second=0, microsecond=0)][hid] = raw or {}
first_seen = {}
for rn in sorted(by_race):
    pulls = by_race[rn]
    last = pulls[max(pulls)]
    flucs = {h: sorted((f.get("time"), f.get("price")) for f in (o.get("flucs") or []) if f.get("time") and f.get("price")) for h, o in last.items()}
    opens = [fl[0][0] for fl in flucs.values() if fl]
    t0 = datetime.fromtimestamp(min(opens) / 1000, timezone.utc) if opens else None
    print(f"## Race {rn}: market opened {fmt(t0)}\n")
    print("| pull | runners priced | bookmakers on the best price (avg) | TAB on the best price | best / open | average / open |\n|---|---|---|---|---|---|")
    for at in sorted(pulls):
        hs = pulls[at]; nb, tab, rb, ra = [], 0, [], []
        for h, o in hs.items():
            bb = o.get("bestBookies") or []; op = o.get("avgOpen")
            nb.append(len(bb)); tab += "tab" in bb
            for b in bb: first_seen.setdefault(b, at)
            if op and o.get("bestNow"): rb.append(o["bestNow"] / op)
            if op and o.get("avgNow"): ra.append(o["avgNow"] / op)
        m = lambda v: f"x{st.mean(v):.3f}" if v else ""
        mins = f" (+{int((at - t0).total_seconds() // 60)} min)" if t0 else ""
        print(f"| {fmt(at)}{mins} | {len(hs)} | {st.mean(nb):.1f} | {tab} of {len(hs)} | {m(rb)} | {m(ra)} |")
    print("\nAverage corporate price from the flucs (Form King's flucs are the average, checked 18 Oct: scripts/fluc_kind.py), against the average open, minutes after the open:\n")
    marks = (5, 15, 30, 60, 120, 240)
    rat = {k: [] for k in marks}
    for h, fl in flucs.items():
        if not fl: continue
        start, p0 = fl[0]
        for k in marks:
            prior = [p for t, p in fl if t <= start + k * 60000]
            if prior and p0: rat[k].append(prior[-1] / p0)
    print("| " + " | ".join(f"+{k} min" for k in marks) + " |\n|" + "---|" * len(marks))
    print("| " + " | ".join(f"x{st.mean(v):.3f}" if v else "" for k, v in rat.items()) + " |\n")
print("## Bookmakers in the order they first held a best price\n")
for b, at in sorted(first_seen.items(), key=lambda x: x[1]):
    print(f"- {b}: {fmt(at)}")
