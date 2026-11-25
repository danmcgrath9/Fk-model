import csv, collections, statistics, math
import numpy as np
S = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad"
R = [r for r in csv.DictReader(open(S + "/rain/tw.csv")) if "synth" not in r["track"]]
fl = lambda x: float(x) if x not in ("", None) else None
for r in R:
    for k in ("first", "last", "wettest", "mode", "rain_d3", "rain_d2", "rain_d1", "rain_day", "rain_3d", "et0_3d", "tmax"):
        r[k] = fl(r[k])
    r["track"] = r["track"].replace("-", " ")
R = [r for r in R if None not in (r["last"], r["first"], r["rain_day"], r["rain_3d"])]
print("meetings", len(R))
# each track's usual rating on a dry week (under 2mm in the 3 days and on the day), else 4
dry = collections.defaultdict(list)
for r in R:
    if r["rain_3d"] + r["rain_day"] < 2: dry[r["track"]].append(r["last"])
base = {t: statistics.median(v) for t, v in dry.items() if len(v) >= 5}
for r in R: r["base"] = base.get(r["track"], 4.0)

def bands(x, cuts):
    for i, c in enumerate(cuts):
        if x < c: return i
    return len(cuts)

print("\n## How the LAST race's rating moves with each day's rain (mean rating above the track's dry usual)")
print("| mm that day | 3 days before | 2 days before | day before | RACE DAY |")
cuts = [1, 5, 10, 20, 30]; lab = ["<1", "1-5", "5-10", "10-20", "20-30", "30+"]
for i, l in enumerate(lab):
    cells = []
    for k in ("rain_d3", "rain_d2", "rain_d1", "rain_day"):
        v = [r["last"] - r["base"] for r in R if bands(r[k], cuts) == i]
        cells.append(f"{statistics.mean(v):+.2f} (n={len(v)})" if len(v) >= 5 else "-")
    print(f"| {l} | " + " | ".join(cells) + " |")

# regression: rating above dry usual on log1p of each day's rain, plus evaporation
def X_of(rs, keys):
    return np.array([[1.0] + [math.log1p(max(r[k], 0)) for k in keys] for r in rs])
y_of = lambda rs, tgt: np.array([r[tgt] - r["base"] for r in rs])
train = [r for r in R if r["date"] < "2025-01-01"]; test = [r for r in R if r["date"] >= "2025-01-01"]
print(f"\ntrain (to 2024) {len(train)} meetings, test (2025-26) {len(test)}")
for tgt in ("first", "last"):
    print(f"\n## Predicting the {tgt.upper()} race's official rating (test years only, 2025-26)")
    print("| model | per-mm weights (log1p) | mean error, rating points | within 1 point | R2 |")
    for name, keys in (("track usual only", []), ("3-day total (the rule's information)", ["rain_3d"]),
                       ("race day only", ["rain_day"]), ("3-day total + race day", ["rain_3d", "rain_day"]),
                       ("each day separately", ["rain_d3", "rain_d2", "rain_d1", "rain_day"])):
        Xt, yt = X_of(train, keys), y_of(train, tgt)
        w = np.linalg.lstsq(Xt, yt, rcond=None)[0]
        Xs, ys = X_of(test, keys), y_of(test, tgt)
        p = Xs @ w; e = np.abs(np.round(p) - ys)
        r2 = 1 - ((p - ys) ** 2).sum() / ((ys - ys.mean()) ** 2).sum()
        ws = ", ".join(f"{k.replace('rain_','')} {v:.2f}" for k, v in zip(keys, w[1:]))
        print(f"| {name} | {ws or '-'} | {e.mean():.2f} | {100*(e<=1).mean():.0f}% | {r2:.2f} |")

print("\n## 3-day rain x race-day rain: the LAST race's official rating (mean; % Soft 5+; % Heavy 8+; n)")
c3 = [5, 15, 25]; l3 = ["3d <5", "3d 5-15", "3d 15-25", "3d 25+"]
cd = [2, 10, 20]; ld = ["day <2", "day 2-10", "day 10-20", "day 20+"]
print("| | " + " | ".join(ld) + " |"); print("|---" * 5 + "|")
for i, l in enumerate(l3):
    cells = []
    for j in range(4):
        v = [r["last"] for r in R if bands(r["rain_3d"], c3) == i and bands(r["rain_day"], cd) == j]
        cells.append(f"{statistics.mean(v):.1f}; {100*sum(x>=5 for x in v)/len(v):.0f}%; {100*sum(x>=8 for x in v)/len(v):.0f}%; n={len(v)}" if v else "-")
    print(f"| {l} | " + " | ".join(cells) + " |")

print("\n## The rule's Soft 5 (3 days 15mm+) against what the track was, by race-day rain")
for j, l in enumerate(ld):
    v = [r["last"] for r in R if r["rain_3d"] >= 15 and bands(r["rain_day"], cd) == j]
    if not v: continue
    c = collections.Counter("Good 4 or firmer" if x <= 4 else "Soft 5" if x == 5 else "Soft 6-7" if x <= 7 else "Heavy 8+" for x in v)
    print(f"- {l} (n={len(v)}): " + ", ".join(f"{k} {100*c[k]/len(v):.0f}%" for k in ("Good 4 or firmer", "Soft 5", "Soft 6-7", "Heavy 8+")))
print("\n## Meetings UNDER the rule's 15mm line, by race-day rain")
for j, l in enumerate(ld):
    v = [r["last"] for r in R if r["rain_3d"] < 15 and bands(r["rain_day"], cd) == j]
    if not v: continue
    c = collections.Counter("Good 4 or firmer" if x <= 4 else "Soft 5" if x == 5 else "Soft 6-7" if x <= 7 else "Heavy 8+" for x in v)
    print(f"- {l} (n={len(v)}): " + ", ".join(f"{k} {100*c[k]/len(v):.0f}%" for k in ("Good 4 or firmer", "Soft 5", "Soft 6-7", "Heavy 8+")))
print("\n## Rating change across the day (first race to last) by race-day rain")
for j, l in enumerate(ld):
    v = [r["last"] - r["first"] for r in R if bands(r["rain_day"], cd) == j and r["races"] and int(r["races"]) >= 4]
    if v: print(f"- {l} (n={len(v)}): mean {statistics.mean(v):+.2f}, worsened in {100*sum(x>0 for x in v)/len(v):.0f}%, by 2+ in {100*sum(x>=2 for x in v)/len(v):.0f}%")
