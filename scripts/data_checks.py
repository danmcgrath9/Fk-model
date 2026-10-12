"""Data checks on an exported dataset (12 Oct 2026, after Dave's export notes: duplicate past runs, Murray Bridge
distances, missing BSP, bad auto-reviewed ratings). Reports; never fails a run. Run after export_dataset:
    python scripts/data_checks.py research/form_gbm/ds/model_ds.npz [--list OUT.csv]
What it checks, and why each one is here:
  1. duplicate past runs: the same race id twice in a runner's past runs, and two runs of the same kind on the same day
     with the same finish under different ids (Dave: inner/main track trial duplicates, and the Murray Bridge resync).
     These inflate the prep and career counts the first-up and second-up features read.
  2. one race, two distances: the same past race id with a different distance in different horses' records (what the
     Murray Bridge resync produced). Non-round distances are not flagged: Form King adjusts for the rail at many tracks.
  3. ratings: past races with no rating, ratings outside the range every other run sits in, and trials with a rating.
  4. BSP: runners in the dataset with no BSP (whole races with none are dropped and counted by export_dataset).
--list writes every flagged past run (horse, race id, check) so the list can be handed to Form King."""
import collections, csv, sys
import numpy as np

path = sys.argv[1]; out = sys.argv[sys.argv.index("--list") + 1] if "--list" in sys.argv else None
D = np.load(path, allow_pickle=True)
P = D["P"].astype(float); f = {str(n): i for i, n in enumerate(D["past_fields"])}
pid = D["past_race_ids"].astype(str); name = D["name"].astype(str); hid = D["horse_id"].astype(str)
n = len(hid); tr = P[:, :, f["trial"]] == 1; held = pid != ""
flags = []
# 1. duplicates, counted once per horse (the same horse appears in many of our races)
seen_h = set(); d_id = d_day_tr = d_day_race = 0
db, fin = P[:, :, f["days_before"]], P[:, :, f["finish"]]
date = D["date"].astype(str); ri = D["race_idx"]
for i in range(n):
    if hid[i] in seen_h or not held[i].any(): continue
    seen_h.add(hid[i]); ok = held[i]
    for rid, c in collections.Counter(pid[i][ok]).items():
        if c > 1: d_id += c - 1; flags.append((name[i], hid[i], rid, "same race id twice"))
    by = collections.defaultdict(list)
    for j in np.where(ok)[0]: by[(db[i, j], fin[i, j], tr[i, j])].append(pid[i, j])
    for (_, _, t), ids in by.items():
        if len(set(ids)) > 1:
            if t: d_day_tr += len(set(ids)) - 1
            else: d_day_race += len(set(ids)) - 1
            flags.append((name[i], hid[i], " / ".join(sorted(set(ids))), "two trials the same day" if t else "two races the same day"))
# 2. one past race, two distances: the same race id carrying a different distance in different horses' records.
# Non-round distances are NOT a fault (Form King adjusts for the rail at Geelong, Sale, Kyneton and others); a race
# disagreeing with itself is, and it is exactly what the Murray Bridge resync produced (Dave, Oct 2026).
dist = P[:, :, f["distance"]]; seen_d = collections.defaultdict(set); runs = set()
for i, j in zip(*np.where(held & ~tr & np.isfinite(dist))): seen_d[pid[i, j]].add(float(dist[i, j])); runs.add(pid[i, j])
odd = sorted((r, sorted(v)) for r, v in seen_d.items() if len(v) > 1)
for r, v in odd: flags.append(("", "", r, "distance differs between records: " + " / ".join(f"{x:.0f}m" for x in v)))
odd_tr = collections.Counter(r.split("_")[0] for r, _ in odd)
# 3. ratings
rat = P[:, :, f["rating"]]; race = held & ~tr
lo, hi = np.nanpercentile(rat[race], [0.1, 99.9]) if np.isfinite(rat[race]).any() else (np.nan, np.nan)
no_rat = len({pid[i, j] for i, j in zip(*np.where(race & ~np.isfinite(rat)))})
out_rat = sorted({(pid[i, j], round(float(rat[i, j]), 1)) for i, j in zip(*np.where(race & np.isfinite(rat) & ((rat < lo - 10) | (rat > hi + 10))))})
for r, v in out_rat: flags.append(("", "", r, f"rating {v} far outside the usual range"))
tr_rat = int((tr & np.isfinite(rat)).sum())
# 4. BSP
bsp = D["bsp"].astype(float); no_bsp = int((~(np.isfinite(bsp) & (bsp > 1))).sum())
print(f"data checks on {path}: {n} runners, {len(seen_h)} horses, {len(runs)} distinct past races held")
print(f"  duplicate past runs: same race id twice {d_id}; same-day trials under two ids {d_day_tr}; same-day races under two ids {d_day_race}")
print(f"  distances: {len(odd)} past races carry two different distances in different records"
      + (f" (most at: {', '.join(f'{t} {c}' for t, c in odd_tr.most_common(5))})" if odd else ""))
print(f"  ratings: {no_rat} past races with no rating; {len(out_rat)} far outside {lo:.0f} to {hi:.0f}; {tr_rat} trial runs carry a rating")
print(f"  BSP: {no_bsp} runners in the dataset without one")
if out:
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["horse", "horse_id", "race_id", "check"]); w.writerows(flags)
    print(f"  wrote {len(flags)} flagged rows to {out}")
