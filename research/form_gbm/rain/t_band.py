import csv, io, collections
S = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad"
f = lambda x: float(x) if x not in ("", None) else None
band = lambda x: 0 if x <= 4 else 1 if x <= 7 else 2
NAMES = ("Good", "Soft", "Heavy")
c3 = [5, 15, 25]; cd = [2, 10, 20]
bins = lambda x, cuts: sum(x >= c for c in cuts)
# the band table from actual rain, meetings BEFORE 2025 (the long 28 Oct file)
H = [r for r in csv.DictReader(open(S + "/rain/tw.csv")) if "synth" not in r["track"] and r["date"] < "2025-01-01"]
tab = collections.defaultdict(collections.Counter)
for r in H:
    if f(r["last"]) is None or f(r["rain_3d"]) is None or f(r["rain_day"]) is None: continue
    tab[(bins(f(r["rain_3d"]), c3), bins(f(r["rain_day"]), cd))][band(f(r["last"]))] += 1
def call(r3, rd, heavy_at=None):
    c = tab[(bins(r3, c3), bins(rd, cd))]; n = sum(c.values())
    if not n: return 0
    if heavy_at is not None and c[2] / n >= heavy_at: return 2
    return max(range(3), key=lambda k: c[k])
print("band table (pre-2025, actual rain): most likely band, P(heavy)")
for i in range(4):
    print("  3d bin", i, [f"{NAMES[max(range(3), key=lambda k: tab[(i, j)][k])]} {100*tab[(i, j)][2]/max(1, sum(tab[(i, j)].values())):.0f}% (n={sum(tab[(i, j)].values())})" for j in range(4)])
t = open(S + "/rain/fc.md").read(); a = t.find("CSV-BEGIN") + 9; b = t.find("CSV-END")
T = [r for r in csv.DictReader(io.StringIO(t[a:b].strip())) if r["date"] >= "2025-01-01"]
for r in T:
    for k in list(r):
        if k not in ("date", "track"): r[k] = f(r[k])
T = [r for r in T if None not in (r["last"], r["era5_d3"], r["era5_d2"], r["era5_d1"], r["era5_day"], r["fc_d2_lead1"], r["fc_d1_lead2"], r["fc_day_lead3"], r["fc_day_lead1"])]
act = [band(r["last"]) for r in T]
print(f"\n2025-26 meetings: {len(T)}; actual bands Good {act.count(0)}, Soft {act.count(1)}, Heavy {act.count(2)}")
def score(name, pred):
    ok = sum(p == x for p, x in zip(pred, act)); hv = sum(1 for p, x in zip(pred, act) if p == 2 and x == 2)
    calls = pred.count(2); wrong_dry = sum(1 for p, x in zip(pred, act) if p >= 1 and x == 0); missed_wet = sum(1 for p, x in zip(pred, act) if p == 0 and x >= 1)
    print(f"| {name} | {100*ok/len(T):.0f}% | {hv} of {act.count(2)} | {calls} ({100*hv/max(calls,1):.0f}% right) | {missed_wet} | {wrong_dry} |")
print("| how the band is called | right band | heavy days called heavy | heavy calls (right) | wet days priced Good | Good days priced wet |")
wed3 = lambda r: r["era5_d3"] + r["fc_d2_lead1"] + r["fc_d1_lead2"]
score("the rule: Soft at 15mm+ in 3 days (Wednesday forecast), else Good", [1 if wed3(r) >= 15 else 0 for r in T])
score("table, Wednesday forecast of 3 days + race day", [call(wed3(r), r["fc_day_lead3"]) for r in T])
score("same, Heavy when 40%+ of such meetings were Heavy", [call(wed3(r), r["fc_day_lead3"], 0.40) for r in T])
score("table, day before: actual 3 days + race-day forecast", [call(r["era5_d3"] + r["era5_d2"] + r["era5_d1"], r["fc_day_lead1"]) for r in T])
score("same, Heavy at 40%+", [call(r["era5_d3"] + r["era5_d2"] + r["era5_d1"], r["fc_day_lead1"], 0.40) for r in T])
score("hindsight: actual 3 days + actual race day", [call(r["era5_d3"] + r["era5_d2"] + r["era5_d1"], r["era5_day"]) for r in T])
print("\n## Only the meetings the rule prices Soft 5 (Wednesday forecast 15mm+ in the 3 days): the official rating plays no part there")
W = [(r, a) for r, a in zip(T, act) if wed3(r) >= 15]
c = collections.Counter(a for _, a in W)
print(f"{len(W)} meetings: finished Good {c[0]}, Soft {c[1]}, Heavy {c[2]}")
p = [call(wed3(r), r["fc_day_lead3"]) for r, _ in W]
print(f"rule (Soft 5): right band {c[1]} of {len(W)}; table with race-day forecast: right band {sum(x == a for x, (_, a) in zip(p, W))} of {len(W)}, Heavy calls {p.count(2)} ({sum(1 for x, (_, a) in zip(p, W) if x == 2 and a == 2)} right)")
for j, l in enumerate(["day <2", "day 2-10", "day 10-20", "day 20+"]):
    v = [a for r, a in W if bins(r["fc_day_lead3"], cd) == j]
    if v: print(f"  Wednesday race-day forecast {l}: n={len(v)}, Good {v.count(0)}, Soft {v.count(1)}, Heavy {v.count(2)}")
