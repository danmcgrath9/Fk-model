"""Our prices against the closing market for one meeting (founder, 19 Oct 2026: "pull the actual results tonight with
BSP and our odds"). DB only, no credits.

    python scripts/meeting_clv.py echuca-20261019 data/live_bets/2026-10-19-echuca-g4-v6.json

Every runner that started (has a BSP): our price (the v6 file's p, renormalised over the starters), Form King's open,
SP, BSP and finish; then, across the meeting, how well our price and the open each predicted the winners against BSP
(log loss on the winner, lower is sharper), and for the runners the live rule would back (open at least 1.2x our price,
our price $1.60-$15) the open against BSP (above 1 = we beat the close)."""
import json, math, os, sys, collections
import psycopg
mid, v6 = sys.argv[1], sys.argv[2]
ours = {(int(r["race"]), r["horse"].lower()): float(r["p"]) for r in json.load(open(v6))}
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute("""select r.race_number, coalesce(e.raw->'horse'->>'name', e.raw->>'horseName', e.raw->>'name'),
                               coalesce(res.finish_position, (e.raw->'horseResult'->>'finishPosition')::int),
                               coalesce(res.starting_price, (e.raw->'horseResult'->>'startingPrice')::numeric),
                               coalesce((res.raw->>'betfairStartingPrice')::numeric, (e.raw->'horseResult'->>'betfairStartingPrice')::numeric),
                               e.raw->'odds'->>'avgOpen'
                        from fk.entries e join fk.races r using (race_id)
                             left join fk.results res on res.race_id = e.race_id and res.horse_id = e.horse_id
                        where r.meeting_id = %s order by r.race_number""", (mid,)).fetchall()
races = collections.defaultdict(list)
for rn, name, fin, sp, bsp, op in rows:
    if bsp and float(bsp) > 1:
        races[rn].append(dict(name=name, fin=fin, sp=float(sp) if sp else None, bsp=float(bsp),
                              open=float(op) if op else None, p=ours.get((rn, (name or "").lower()))))
print(f"# {mid}: our price against the close\n")
print("| race | horse | ours | open | SP | BSP | finish | open / BSP |\n|---|---|---|---|---|---|---|---|")
ll_us = ll_open = ll_bsp = 0.0; nwin = 0; backed = []
for rn in sorted(races):
    rs = races[rn]
    if any(x["p"] is None for x in rs): print(f"| R{rn} | (a starter missing from our file, race skipped) | | | | | | |"); continue
    s = sum(x["p"] for x in rs); sb = sum(1 / x["bsp"] for x in rs)
    so = sum(1 / x["open"] for x in rs if x["open"]) if all(x["open"] for x in rs) else None
    for x in rs:
        q = x["p"] / s; ours_price = 1 / q
        rule = x["open"] and 1.6 <= ours_price <= 15 and x["open"] >= 1.2 * ours_price
        if rule: backed.append(x["open"] / x["bsp"])
        if x["fin"] == 1:
            nwin += 1; ll_us -= math.log(q); ll_bsp -= math.log((1 / x["bsp"]) / sb)
            if so: ll_open -= math.log((1 / x["open"]) / so)
        mark = " **(value at open)**" if rule else ""
        print(f"| R{rn} | {x['name']}{mark} | ${ours_price:.2f} | {'$%.2f' % x['open'] if x['open'] else ''} | {'$%.2f' % x['sp'] if x['sp'] else ''} | ${x['bsp']:.2f} | {x['fin'] or ''} | {'%.2f' % (x['open'] / x['bsp']) if x['open'] else ''} |")
print(f"\nWinners scored: {nwin}. Log loss on the winner (lower = sharper): ours {ll_us / max(nwin, 1):.3f}, "
      f"open {ll_open / max(nwin, 1):.3f}, BSP {ll_bsp / max(nwin, 1):.3f}")
if backed:
    print(f"Value-at-open runners: {len(backed)}, open / BSP average {sum(backed) / len(backed):.2f}, "
          f"beat BSP on {sum(b > 1 for b in backed)} of {len(backed)}")
