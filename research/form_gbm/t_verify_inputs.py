"""Recompute model inputs straight from the raw Form King race files and compare them with the dataset the model is
trained on (15 Oct 2026, founder: "make sure what we are doing is right and we aren't assuming anything").
python3.13 t_verify_inputs.py RAW_DAY.jsonl.gz [more days]"""
import gzip, json, sys, numpy as np, collections
Z = np.load("ds/model_ds_new.npz", allow_pickle=True)
ri = Z["race_idx"]; rid = Z["race_id"].astype(str); hid = Z["horse_id"].astype(str); cols = list(Z["cols"]); pf = list(Z["past_fields"])
row = {(rid[ri[i]], hid[i]): i for i in range(len(ri))}
X = Z["X"]; P = Z["P"]
bad = collections.Counter(); checked = collections.Counter(); ex = collections.defaultdict(list)
def cmp(name, a, b, i, tol=1e-3):
    checked[name] += 1
    if a is None and (b is None or np.isnan(float(b))): return
    try:
        if a is not None and b is not None and not np.isnan(float(b)) and abs(float(a) - float(b)) <= tol: return
    except (TypeError, ValueError): pass
    bad[name] += 1
    if len(ex[name]) < 3: ex[name].append((i, a, b))
def num(v):
    try: f = float(v); return f if np.isfinite(f) else None
    except (TypeError, ValueError): return None
import importlib.util
sys.path.insert(0, "/home/user/fk-model"); from fk import fields as F
for path in sys.argv[1:]:
    for line in gzip.open(path, "rt"):
        bnd = json.loads(line); rdate = str(bnd["date"])[:10]
        for e in bnd["entries"]:
            i = row.get((bnd["race_id"], F.horse_id(e)))
            if i is None: continue
            hr = e.get("horseResult") or {}
            cmp("target: finish", num(hr.get("finishPosition")), float(Z["finish"][i]), i)
            cmp("target: BSP", num(hr.get("betfairStartingPrice")), Z["bsp"][i], i, 0.01)
            cmp("target: opening price (odds.avgOpen)", num((e.get("odds") or {}).get("avgOpen")), Z["open"][i], i, 0.01)
            for k in ("barrier", "weight", "daysSinceLastRace", "apprenticeClaim"):
                cmp(f"entry: {k}", num(e.get(k)), X[i, cols.index(k)] if k in cols else np.nan, i)
            g = [x for x in e.get("gear") or [] if isinstance(x, dict)]
            cmp("gear: first-time ON count (correct meaning)", float(sum(x.get("change") == "ON_FIRST_TIME" for x in g)), X[i, cols.index("gear_first_time")], i)
            cmp("gear: blinkers ON first time (correct meaning)", float(any("blink" in str(x.get("gear")).lower() and x.get("change") == "ON_FIRST_TIME" for x in g)), X[i, cols.index("blinkers_first")], i)
            runs = sorted([(F.past_event_date(p), p) for p in F.entry_past_events(e)
                           if not (str(p.get("scratched")).lower() == "true") and F.past_event_date(p) and F.past_event_date(p) < rdate],
                          key=lambda t: t[0], reverse=True)[:10]
            from datetime import date
            for j, (d, p) in enumerate(runs):
                cmp("past run: days before", float((date.fromisoformat(rdate) - date.fromisoformat(d[:10])).days), P[i, j, pf.index("days_before")], i)
                fp = num(p.get("finishPosition")); cmp("past run: finish", fp if fp and fp > 0 else None, P[i, j, pf.index("finish")], i)
                cmp("past run: margin", num(p.get("margin")), P[i, j, pf.index("margin")], i, 0.01)
                bs = num(p.get("bsp")); cmp("past run: BSP", bs if bs and bs > 1 else None, P[i, j, pf.index("bsp")], i, 0.01)
                cmp("past run: barrier", num(p.get("barrier")), P[i, j, pf.index("barrier")], i)
                st = num(p.get("posSettling")); cmp("past run: settling position", st if st and st > 0 else None, P[i, j, pf.index("settle")], i)
            for j in range(len(runs), 10):
                cmp("past run: empty slot stays empty", None, P[i, j, pf.index("days_before")], i)
print("| check | values checked | mismatches | example (row, raw, dataset) |\n|---|---|---|---|")
for k in checked: print(f"| {k} | {checked[k]} | {bad[k]} | {ex[k][:2] if bad[k] else ''} |")
dbp = P[:, :, pf.index("days_before")]; print(f"\nleak check, whole dataset: smallest 'days before' of any past run = {np.nanmin(dbp):.0f} (must be 1 or more)")
