"""When TAB's markets open, by meeting (scripts/open_times.py output). For each meeting: the race day, the day and clock
time its first race opened and its last race opened, and how that sits against the 12:17pm pricing run.
    python3.13 open_times_report.py open_times.md"""
import collections, csv, sys, io
import datetime as dt
txt = open(sys.argv[1]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip()
rows = list(csv.DictReader(io.StringIO(txt)))
M = collections.defaultdict(list)
for r in rows:
    if int(r["within10"]) < 0.6 * int(r["runners_priced"]): continue        # one early quote is not an opening market
    M[(r["date"], r["track"])].append(r)
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; METRO = ("flemington", "caulfield", "caulfield heath", "moonee valley", "sandown hillside", "sandown lakeside")
out = []
for (d, trk), rs in sorted(M.items()):
    opens = sorted(dt.datetime.strptime(r["open_mel"], "%Y-%m-%d %H:%M") for r in rs); race = dt.date.fromisoformat(d)
    first, last = opens[0], opens[-1]; db = (race - first.date()).days
    out.append(dict(date=d, track=trk, wd=WD[race.weekday()], races=len(rs), days_before=db, first=first, last=last, metro=trk.lower() in METRO,
                    span_min=(last - first).total_seconds() / 60))
print(f"{len(out)} meetings with timed opening markets, {out[0]['date']} to {out[-1]['date']}\n")
print("| race day | track | races | market opened | days before | first race opened | last race opened | minutes first to last |\n|---|---|---|---|---|---|---|---|")
for o in out:
    print(f"| {o['wd']} {o['date'][5:]} | {o['track']} | {o['races']} | {WD[o['first'].weekday()]} | {o['days_before']} | {o['first']:%H:%M} | {o['last']:%a %H:%M} | {o['span_min']:.0f} |")
print("\nCLOCK TIME OF THE FIRST RACE'S OPEN (Melbourne), all meetings:")
b = collections.Counter()
for o in out:
    h = o["first"].hour + o["first"].minute / 60
    b["before 9:00" if h < 9 else "9:00-10:00" if h < 10 else "10:00-11:00" if h < 11 else "11:00-12:17" if h < 12.2833 else "12:17-14:00" if h < 14 else "14:00-17:00" if h < 17 else "after 17:00"] += 1
for k in ("before 9:00", "9:00-10:00", "10:00-11:00", "11:00-12:17", "12:17-14:00", "14:00-17:00", "after 17:00"): print(f"  {k:12s} {b[k]:3d} meetings ({100*b[k]/len(out):.0f}%)")
print("\nDAYS BEFORE THE RACE DAY that the market opened, by race day of the week:")
t = collections.defaultdict(collections.Counter)
for o in out: t[o["wd"]][o["days_before"]] += 1
for wd in WD:
    if t[wd]: print(f"  {wd}: " + ", ".join(f"{k} days before: {v}" for k, v in sorted(t[wd].items())))
