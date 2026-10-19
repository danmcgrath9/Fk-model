"""Our bets in an odds watch: for named runners, every stored pull of Form King's odds (open, best now and who holds it,
average now). Founder, 19 Oct 2026: "I mean every horse we were on". DB only, no credits.

    python scripts/odds_watch_ours.py 2026-10-21 Geelong "5:Murshidi" "8:Some Horse" ..."""
import os, sys
from datetime import timezone, timedelta
import psycopg
MEL = timezone(timedelta(hours=11))
day, track, picks = sys.argv[1], sys.argv[2], [a.split(":", 1) for a in sys.argv[3:]]
mid = f"{track.lower().replace(' ', '-')}-{day.replace('-', '')}"
print(f"# Our runners: {track} {day}\n")
print("| race | horse | pull | open (avg) | best now | best / open | bookmakers on best | average now | avg / open |\n|---|---|---|---|---|---|---|---|---|")
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for rn, name in picks:
        rows = c.execute("""select s.fetched_at, s.raw from fk.odds_snapshots s join fk.races r using (race_id)
                            join fk.horses h on h.horse_id = s.horse_id
                            where r.meeting_id = %s and r.race_number = %s and lower(h.name) = lower(%s) and s.kind = 'current'
                            order by s.fetched_at""", (mid, int(rn), name)).fetchall()
        if not rows:
            print(f"| R{rn} | {name} | no snapshots | | | | | | |"); continue
        for at, o in rows:
            o = o or {}; op, bn, an = o.get("avgOpen"), o.get("bestNow"), o.get("avgNow"); bb = o.get("bestBookies") or []
            r = lambda x: f"x{x / op:.2f}" if op and x else ""
            print(f"| R{rn} | {name} | {at.astimezone(MEL).strftime('%H:%M')} | {op or ''} | {bn or ''} | {r(bn)} | "
                  f"{', '.join(bb[:6])}{' +' + str(len(bb) - 6) if len(bb) > 6 else ''} | {an or ''} | {r(an)} |")
