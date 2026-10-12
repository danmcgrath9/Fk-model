"""What a meeting costs us in Form King credits, from the ledger. DB only, no credits.
Groups live calls by Melbourne day and the meeting/race id in their args, and prints the per-day total and the
per-meeting breakdown by operation.    python scripts/credit_costs.py [DAYS]"""
import os, sys, json, collections
import psycopg
days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
with psycopg.connect(os.environ["DATABASE_URL"].strip()) as c:
    rows = c.execute("""select (called_at at time zone 'Australia/Melbourne')::date, operation, credits, args
                        from fk.ledger where key_kind='live' and called_at > now() - (%s || ' days')::interval
                        order by called_at""", (str(days),)).fetchall()
by_day = collections.Counter(); by_meet = collections.defaultdict(collections.Counter); ops = collections.Counter()
for d, op, cr, args in rows:
    a = args if isinstance(args, dict) else (json.loads(args) if args else {})
    m = a.get("meetingId") or (a.get("raceId", "")[:4].lower() + "-" + str(a.get("raceId", ""))[5:11] if a.get("raceId") else "other")
    by_day[str(d)] += cr; by_meet[m][op] += cr; ops[op] += cr
print("| day | credits |"); print("|---|---|")
for d in sorted(by_day): print(f"| {d} | {by_day[d]} |")
print("\n| meeting | total | by operation |"); print("|---|---|---|")
for m, c in sorted(by_meet.items(), key=lambda kv: -sum(kv[1].values()))[:25]:
    print(f"| {m} | {sum(c.values())} | " + ", ".join(f"{k} {v}" for k, v in c.most_common()) + " |")
print("\ntotal", sum(ops.values()), dict(ops))
