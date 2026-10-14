"""How far from BSP the market is at each point after the open, beside our price, on the same races (15 Oct 2026,
founder: "how far from bsp are we and opening market and 2 minutes after, 5, 10, 20"). Prices from Form King's timed
flucs (fluc_timing.py: m = minutes after the open, a = hours after the open, b = hours before the jump); BSP, results
and our holdout price (stage-2 v6, p2) from the dataset. KL to BSP per race (lower = closer) and log loss vs winners."""
import csv, numpy as np, bench as b, collections, sys
D = b.load(); z = np.load("blend_hold.npz"); ri = D["race_idx"]
rid = D["race_id"].astype(str); hid = D["horse_id"].astype(str)
key = {(rid[ri[i]], hid[i]): i for i in range(len(ri))}
rows = list(csv.DictReader(open(sys.argv[1])))
cols = [("Our price", None), ("Opening price", "open"), ("2 min after open", "m2"), ("5 min", "m5"), ("10 min", "m10"), ("20 min", "m20"),
        ("1 hour after open", "a1"), ("4 hours", "a4"), ("12 hours", "a12"), ("3 hours before jump", "b3"), ("1 hour before jump", "b1"), ("last fluc", "last")]
by = collections.defaultdict(list)
for r in rows:
    i = key.get((r["race_id"], r["horse_id"]))
    if i is not None and str(r.get("scratched", "")).lower() not in ("true", "1"): by[r["race_id"]].append((r, i))
def f(v):
    try: v = float(v); return v if v > 1 else None
    except (TypeError, ValueError): return None
res = {c: [0.0, 0.0, 0] for c, _ in cols}; nr = 0; bsp_ll = 0.0
for race, rr in by.items():
    idx = [i for _, i in rr]
    if len(set(ri[idx])) != 1 or len(idx) != (ri == ri[idx[0]]).sum(): continue   # every runner of the race present
    q = D["q"][idx]; won = D["finish"][idx] == 1
    if not (q > 0).all() or won.sum() != 1: continue
    P = {}
    for c, k in cols:
        if k is None: p = z["p2"][idx]
        else:
            pr = [f(r[k]) for r, _ in rr]
            if any(x is None for x in pr): break
            p = 1 / np.array(pr)
        P[c] = p / p.sum()
    else:
        nr += 1; bsp_ll += float(-np.log(q[won][0]))
        for c, p in P.items():
            res[c][0] += float(np.sum(q * np.log(q / p))); res[c][1] += float(-np.log(p[won][0])); res[c][2] += 1
print(f"{nr} races with every runner priced at every point\n\n| price | KL to BSP | log loss vs winners |\n|---|---|---|")
for c, _ in cols:
    s = res[c]; print(f"| {c} | {s[0]/s[2]:.4f} | {s[1]/s[2]:.4f} |")
print(f"| Betfair SP | 0 | {bsp_ll/nr:.4f} |")
