"""Score replay_stale.npz: stale v fresh history, stage 1 and stage 2, against BSP and winners, by week; then the committed
live files against the stale replay (same trees, same stale history: the difference is pre-race v rebuilt inputs).
    python3.13 score_replay.py"""
import collections, json, os, sys
import numpy as np
sys.path.insert(0, "/home/user/fk-model/research/form_gbm")
import track_rules as tr

Z = np.load("ds/model_ds.npz", allow_pickle=True); R = np.load("replay_stale.npz")
ri = Z["race_idx"]; nR = len(Z["race_id"]); rdate = Z["date"].astype(str); date = rdate[ri]
bs = Z["bsp"].astype(float); op = Z["open"].astype(float); won = Z["finish"] == 1


def norm(inv):
    ok = np.isfinite(inv) & (inv > 0); tot = np.bincount(ri, weights=np.where(ok, inv, 0), minlength=nR)
    full = np.bincount(ri, weights=~ok, minlength=nR) == 0
    return np.where(ok, inv, 0) / np.maximum(tot[ri], 1e-12), full


q, qfull = norm(np.where(bs > 1, 1 / bs, np.nan)); mk, mfull = norm(np.where(op > 1, 1 / op, np.nan))
onew = np.bincount(ri, weights=won, minlength=nR) == 1


def sc(p, m):
    """KL to BSP per race and winner log loss, runners in m (whole races with a full BSP book and one winner)"""
    g = m & qfull[ri] & onew[ri] & np.isfinite(p)
    races = len(np.unique(ri[g]))
    if not races: return np.nan, np.nan, 0
    kl = np.sum(np.where(q[g] > 0, q[g] * np.log(np.maximum(q[g], 1e-300) / np.maximum(p[g], 1e-12)), 0)) / races
    return kl, -np.mean(np.log(np.maximum(p[g & won], 1e-12))), races


live = date > "2026-10-14"; have = np.isfinite(R["stale"][:, 3]) & np.isfinite(R["fresh"][:, 3])
print(f"races 15 Oct - 9 Nov with both arms: {len(np.unique(ri[live & have]))}; runners {int((live & have).sum())}\n")
print("| price (frozen live v10 models, no-network blend) | KL to BSP | winner log loss | races |\n|---|---|---|---|")
for lab, arm, col in (("stage 1, STALE history (to 14 Oct)", "stale", 2), ("stage 1, FRESH history", "fresh", 2),
                      ("stage 2, STALE history (what live does)", "stale", 3), ("stage 2, FRESH history", "fresh", 3)):
    k, l, n = sc(R[arm][:, col], live & have); print(f"| {lab} | {k:.4f} | {l:.4f} | {n} |")
k, l, n = sc(mk, live & have & mfull[ri]); print(f"| the opening market (races with every open) | {k:.4f} | {l:.4f} | {n} |")
k, l, n = sc(q, live & have); print(f"| BSP itself | 0.0000 | {l:.4f} | {n} |")

print("\nBy week (stage 2 KL to BSP: stale / fresh, and stage 1):")
for lo, hi in (("2026-10-15", "2026-10-22"), ("2026-10-22", "2026-10-29"), ("2026-10-29", "2026-11-05"), ("2026-11-05", "2026-11-10")):
    m = have & (date >= lo) & (date < hi)
    a, b_ = sc(R["stale"][:, 3], m), sc(R["fresh"][:, 3], m); c, d = sc(R["stale"][:, 2], m), sc(R["fresh"][:, 2], m)
    print(f"  {lo}..{hi}: {a[2]:3d} races  stage 2 {a[0]:.4f} / {b_[0]:.4f} ({100*(b_[0]/a[0]-1):+.1f}%)  log loss {a[1]:.4f} / {b_[1]:.4f}"
          f"   stage 1 {c[0]:.4f} / {d[0]:.4f}")

# how far apart are the two stage-2 prices, runner by runner?
m = live & have; d = np.abs(np.log(R["fresh"][m, 3] / R["stale"][m, 3]))
print(f"\nfresh v stale stage-2 price, runner by runner: median {100*np.median(d):.1f}% apart, 90th pct {100*np.percentile(d, 90):.1f}%, "
      f"over 10% apart {100*np.mean(d > 0.0953):.0f}% of runners, over 20% {100*np.mean(d > 0.182):.0f}%")
# when they disagree, who is nearer BSP?
big = m & (np.abs(np.log(R["fresh"][:, 3] / R["stale"][:, 3])) > 0.0953) & (q > 0) & qfull[ri]
ef, es = np.abs(np.log(R["fresh"][big, 3] / q[big])), np.abs(np.log(R["stale"][big, 3] / q[big]))
print(f"where they are 10%+ apart ({int(big.sum())} runners): fresh is nearer BSP {100*np.mean(ef < es):.0f}% of the time "
      f"(median distance to BSP: fresh {100*np.median(ef):.0f}%, stale {100*np.median(es):.0f}%)")

# ---- the committed live files against the stale replay --------------------------------------------------------------
key = {(str(Z["race_id"][ri[i]]), str(Z["horse_id"][i])): i for i in np.where(live)[0]}
LIVE = {k: np.full(len(ri), np.nan) for k in ("p_trees", "p_cb", "p_stage1", "p_model", "p")}
used = 0
for pre, (ts, tag, f) in sorted(tr.model_files().items()):
    if pre[:10] <= "2026-10-14": continue
    rows = json.load(open(f)); used += 1
    for r in rows:
        i = key.get((r.get("race_id"), r.get("horse_id")))
        if i is None: continue
        for k in LIVE:
            v = r.get(k, r.get("p") if k == "p_model" else None)
            if v is not None: LIVE[k][i] = v
# renormalise each live price over the runners that ran (late scratchings leave the file's race under 100%)
cov = np.isfinite(LIVE["p_model"]); racefull = np.bincount(ri, weights=~cov, minlength=nR) == 0
for k in LIVE:
    v = np.where(np.isfinite(LIVE[k]), LIVE[k], 0); tot = np.bincount(ri, weights=v, minlength=nR)
    LIVE[k] = np.where(racefull[ri] & (tot[ri] > 0), v / np.maximum(tot[ri], 1e-12), np.nan)
ml = live & have & racefull[ri] & np.isfinite(LIVE["p_trees"])
print(f"\nCOMMITTED LIVE FILES ({used} meetings' files from 15 Oct): races where every runner that ran is in the file: {len(np.unique(ri[ml]))}")
print("| price | KL to BSP | winner log loss | races |\n|---|---|---|---|")
for lab, p in (("live file: trees (pre-race inputs, stale history)", LIVE["p_trees"]), ("replay: trees, stale history (rebuilt inputs)", R["stale"][:, 0]),
               ("replay: trees, fresh history (rebuilt inputs)", R["fresh"][:, 0]),
               ("live file: stage 1 three-way (with the network)", LIVE["p_stage1"]), ("replay: stage 1 no-network, stale", R["stale"][:, 2]),
               ("live file: stage 2 = our price before the open blend", LIVE["p_model"]), ("replay: stage 2, stale", R["stale"][:, 3]),
               ("replay: stage 2, fresh", R["fresh"][:, 3]), ("live file: blended with the open (the betting price)", LIVE["p"]),
               ("opening market", np.where(mfull[ri], mk, np.nan))):
    k, l, n = sc(p, ml & np.isfinite(p)); print(f"| {lab} | {k:.4f} | {l:.4f} | {n} |")
d = np.abs(np.log(LIVE["p_trees"][ml] / R["stale"][ml, 0]))
print(f"\nlive trees v the stale replay's trees (same model, same stale history; only the inputs differ), {int(ml.sum())} runners: "
      f"median {100*np.median(d):.1f}% apart, 90th pct {100*np.percentile(d, 90):.1f}%, over 10% apart {100*np.mean(d > 0.0953):.0f}%")
np.savez("live_join.npz", **LIVE)
