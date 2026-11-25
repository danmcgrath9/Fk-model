import csv, io, math, statistics, collections
import numpy as np
S = "/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad"
t = open(S + "/rain/fc.md").read(); a = t.find("CSV-BEGIN") + 9; b = t.find("CSV-END")
R = list(csv.DictReader(io.StringIO(t[a:b].strip())))
f = lambda x: float(x) if x not in ("", None) else None
for r in R:
    for k in list(r):
        if k not in ("date", "track"): r[k] = f(r[k])
print("rows", len(R), "with lead-3 race-day forecast", sum(r["fc_day_lead3"] is not None for r in R), "last rating", sum(r["last"] is not None for r in R))
print(t[:t.find("CSV-BEGIN")].splitlines()[-2:])
# 1. how well is each day's rain forecast, by lead, against ERA5 (what the rating test used) and the forecast model's own rain
def skill(fk, ak, thr=10):
    v = [(r[fk], r[ak]) for r in R if r[fk] is not None and r[ak] is not None]
    if len(v) < 30: return None
    x = np.array([p for p, _ in v]); y = np.array([q for _, q in v])
    hit = ((x >= thr) & (y >= thr)).sum(); obs = (y >= thr).sum(); fcy = (x >= thr).sum()
    return dict(n=len(v), r=np.corrcoef(x, y)[0, 1], mae=np.abs(x - y).mean(), pod=hit / obs if obs else float("nan"),
                far=1 - hit / fcy if fcy else float("nan"), obs=obs)
print("\n## Race-day rain: forecast N days ahead against what fell (ERA5; 10mm+ = a wet day)")
print("| lead | n | correlation | avg miss mm | wet days caught | forecast wet days that were wet |")
for n in (1, 2, 3, 4, 5):
    s = skill(f"fc_day_lead{n}", "era5_day")
    if s: print(f"| {n} day{'s' if n>1 else ''} | {s['n']} | {s['r']:.2f} | {s['mae']:.1f} | {100*s['pod']:.0f}% of {s['obs']} | {100*(1-s['far']):.0f}% |")
print("\n## The same against the forecast model's own final rain (om_day)")
for n in (1, 2, 3, 4, 5):
    s = skill(f"fc_day_lead{n}", "om_day")
    if s: print(f"| {n} | {s['n']} | {s['r']:.2f} | {s['mae']:.1f} | {100*s['pod']:.0f}% of {s['obs']} | {100*(1-s['far']):.0f}% |")
print("\n## Is race day harder to forecast than the days before it? correlation with ERA5 at the same lead")
print("| lead | 3 days before | 2 days before | day before | race day |")
for n in (1, 2, 3):
    cells = []
    for off, ak in ((3, "era5_d3"), (2, "era5_d2"), (1, "era5_d1"), (0, "era5_day")):
        s = skill(f"fc_{'day' if off == 0 else 'd' + str(off)}_lead{n}", ak)
        cells.append(f"{s['r']:.2f}" if s else "-")
    print(f"| {n} | " + " | ".join(cells) + " |")
# 2. predicting the LAST race's rating from what we would have known
base = collections.defaultdict(list)
for r in R:
    if r["last"] is not None and (r["era5_d3"] or 0) + (r["era5_d2"] or 0) + (r["era5_d1"] or 0) + (r["era5_day"] or 0) < 2: base[r["track"]].append(r["last"])
B = {k: statistics.median(v) for k, v in base.items() if len(v) >= 4}
L = lambda x: math.log1p(max(x, 0))
scen = {
 "hindsight: actual 3 days + actual race day": lambda r: [r["era5_d3"], r["era5_d2"], r["era5_d1"], r["era5_day"]],
 "Wednesday for Saturday: 3-day forecast total only (the rule)": lambda r: [(r["era5_d3"] or 0) + (r["fc_d2_lead1"] or 0) + (r["fc_d1_lead2"] or 0)],
 "Wednesday for Saturday: each day's forecast incl. race day": lambda r: [r["era5_d3"], r["fc_d2_lead1"], r["fc_d1_lead2"], r["fc_day_lead3"]],
 "Day before: actual 3 days + race-day forecast (1 day out)": lambda r: [r["era5_d3"], r["era5_d2"], r["era5_d1"], r["fc_day_lead1"]],
}
rows = [r for r in R if r["last"] is not None and all(r[k] is not None for k in ("era5_d3", "era5_d2", "era5_d1", "era5_day", "fc_d2_lead1", "fc_d1_lead2", "fc_day_lead3", "fc_day_lead1"))]
tr = [r for r in rows if r["date"] < "2025-01-01"]; te = [r for r in rows if r["date"] >= "2025-01-01"]
print(f"\n## Predicting the last race's official rating (fitted on 2024, {len(tr)} meetings; tested on 2025-26, {len(te)})")
print("| what we know | avg miss (points) | within 1 point | right band (good/soft/heavy) | heavy days called heavy |")
band = lambda x: 0 if x <= 4 else 1 if x <= 7 else 2
for name, fn in [("track usual only", lambda r: [])] + list(scen.items()):
    X = lambda rs: np.array([[1.0] + [L(v) for v in fn(r)] for r in rs]); y = lambda rs: np.array([r["last"] - B.get(r["track"], 4.0) for r in rs])
    w = np.linalg.lstsq(X(tr), y(tr), rcond=None)[0]
    p = X(te) @ w + np.array([B.get(r["track"], 4.0) for r in te]); act = np.array([r["last"] for r in te])
    pr = np.clip(np.round(p), 1, 10); e = np.abs(pr - act)
    bp = np.array([band(x) for x in pr]); ba = np.array([band(x) for x in act])
    hv = (ba == 2).sum()
    print(f"| {name} | {e.mean():.2f} | {100*(e<=1).mean():.0f}% | {100*(bp==ba).mean():.0f}% | {100*((bp==2)&(ba==2)).sum()/hv:.0f}% of {hv} |")
# the rule as written: Soft 5 at 15mm+ (Wednesday forecast of the 3 days), else the track's usual
p = np.array([5 if (r["era5_d3"] or 0) + r["fc_d2_lead1"] + r["fc_d1_lead2"] >= 15 else B.get(r["track"], 4.0) for r in te]); act = np.array([r["last"] for r in te])
bp = np.array([band(x) for x in p]); ba = np.array([band(x) for x in act])
print(f"| the rule as written (Soft 5 at 15mm+, else the track's usual) | {np.abs(p-act).mean():.2f} | {100*(np.abs(p-act)<=1).mean():.0f}% | {100*(bp==ba).mean():.0f}% | {100*((bp==2)&(ba==2)).sum()/(ba==2).sum():.0f}% of {(ba==2).sum()} |")
