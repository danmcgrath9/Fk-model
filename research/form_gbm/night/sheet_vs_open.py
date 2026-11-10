"""Was the order sheet ready before the market opened? (night of 10 Nov 2026). For each live meeting: when its first
order sheet (data/live_bets/<prefix>-betmatic-preopen.csv) was first committed, against the time each race's market
opened (scripts/open_times.py). A race that opened before the sheet existed could not have been bet at the open, bot or
no bot. Commit times are the session's, so "ready" is within minutes of the commit.
    python3.13 sheet_vs_open.py open_times.md"""
import collections, csv, glob, io, os, subprocess, sys
import datetime as dt
from zoneinfo import ZoneInfo
MEL = ZoneInfo("Australia/Melbourne"); L = "/home/user/fk-model/data/live_bets"; REPO = "/home/user/fk-model"
rows = list(csv.DictReader(io.StringIO(open(sys.argv[1]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip())))
by = collections.defaultdict(list)
for r in rows:
    if int(r["within10"]) < 0.6 * int(r["runners_priced"]): continue
    by[(r["date"], r["track"].lower().replace(" ", "-"))].append(dt.datetime.strptime(r["open_mel"], "%Y-%m-%d %H:%M").replace(tzinfo=MEL))
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]; out = []
for f in sorted(glob.glob(f"{L}/2026-1*-betmatic-preopen.csv")):
    pre = os.path.basename(f)[:-21]; day, trk = pre[:10], pre[11:]
    ts = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--", f], capture_output=True, text=True, cwd=REPO).stdout.strip().split("\n")[-1]
    if not ts or (day, trk) not in by: continue
    sheet = dt.datetime.fromisoformat(ts).astimezone(MEL); opens = sorted(by[(day, trk)])
    missed = sum(1 for o in opens if o < sheet); lead = (opens[0] - sheet).total_seconds() / 3600
    out.append((day, trk, sheet, opens[0], opens[-1], len(opens), missed, lead))
print(f"{len(out)} live meetings with an order sheet and timed opens\n")
print("| race day | track | sheet committed | first race opened | last race opened | races | opened BEFORE the sheet | sheet ahead of the first open |\n|---|---|---|---|---|---|---|---|")
for day, trk, sheet, o0, o1, n, missed, lead in out:
    d = dt.date.fromisoformat(day)
    print(f"| {WD[d.weekday()]} {day[5:]} | {trk} | {sheet:%a %H:%M} | {o0:%a %H:%M} | {o1:%a %H:%M} | {n} | {missed if missed else ''} | {('%.1f h' % lead) if lead > 0 else 'LATE by %.1f h' % -lead} |")
tot = sum(o[5] for o in out); miss = sum(o[6] for o in out); late_m = sum(1 for o in out if o[6])
print(f"\nraces: {tot}; opened before our sheet existed: {miss} ({100*miss/tot:.0f}%), in {late_m} of {len(out)} meetings ({sum(1 for o in out if o[6] == o[5])} meetings missed whole)")
bywd = collections.defaultdict(lambda: [0, 0])
for o in out:
    w = WD[dt.date.fromisoformat(o[0]).weekday()]; bywd[w][0] += o[5]; bywd[w][1] += o[6]
print("by race day: " + ", ".join(f"{w} {bywd[w][1]} of {bywd[w][0]} races" for w in WD if bywd[w][0]))
