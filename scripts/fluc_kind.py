"""Are Form King's entry flucs the AVERAGE or the BEST corporate price? For every stored runner with flucs, compare the
first fluc with avgOpen and the last fluc with avgNow and bestNow. DB only, no credits.
    python scripts/fluc_kind.py kyneton-20261020 caulfield-20261014"""
import os, sys, psycopg
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    for mid in sys.argv[1:]:
        rows = c.execute("""select e.raw from fk.entries e join fk.races r using (race_id) where r.meeting_id = %s""", (mid,)).fetchall()
        n = f_open = l_avg = l_best = 0
        for (raw,) in rows:
            o = (raw or {}).get("odds") or {}; fl = sorted((f["time"], f["price"]) for f in (o.get("flucs") or []) if f.get("time") and f.get("price"))
            if not fl or not o.get("avgOpen") or not o.get("avgNow") or not o.get("bestNow"): continue
            n += 1; first, last = fl[0][1], fl[-1][1]
            f_open += abs(first - o["avgOpen"]) < 0.011
            l_avg += abs(last - o["avgNow"]) < 0.011; l_best += abs(last - o["bestNow"]) < 0.011
        print(f"{mid}: {n} runners | first fluc = avgOpen {f_open} | last fluc = avgNow {l_avg} | last fluc = bestNow {l_best}")
