import collections, json, sys
import numpy as np
sys.path.insert(0, "/home/user/fk-model/research/form_gbm")
import track_rules as tr
Z = np.load("ds/model_ds.npz", allow_pickle=True); LJ = np.load("live_join.npz"); R = np.load("replay_stale.npz")
ri = Z["race_idx"]; nR = len(Z["race_id"]); rdate = Z["date"].astype(str); date = rdate[ri]
bs = Z["bsp"].astype(float); won = Z["finish"] == 1; fsr = Z["X"][:, list(Z["cols"]).index("firstStarter")] == 1
nfile = collections.Counter()
for pre, (ts, tag, f) in sorted(tr.model_files().items()):
    if pre[:10] <= "2026-10-14": continue
    for r in json.load(open(f)): nfile[r["race_id"]] += 1
nran = np.bincount(ri, minlength=nR); late = np.array([nfile.get(str(Z["race_id"][r]), 0) - nran[r] for r in range(nR)])[ri] > 0
def rules(pm, lab):
    ours = 1 / np.maximum(np.nan_to_num(pm, nan=1e-12), 1e-12); ok = np.isfinite(pm) & np.isfinite(bs) & ~fsr & (date > "2026-10-14")
    print(lab)
    for name, m in (("lay $8-$12 at 1.6x ours", ok & (bs >= 8) & (bs < 12) & (bs >= 1.6 * ours)), ("lay $15-$40 at 1.5x ours", ok & (bs >= 15) & (bs <= 40) & (bs >= 1.5 * ours))):
        for g, gm in (("late scratching in the race", late), ("no late scratching", ~late)):
            x = m & gm; u = np.where(won[x], -(bs[x] - 1), 0.92)
            print(f"  {name:26s} {g:28s} {int(x.sum()):4d} lays, {int(won[x].sum()):2d} won (BSP expected {np.sum(1/bs[x]):4.1f}), {u.sum():+7.2f}u")
rules(LJ["p_model"], "LIVE committed price (re-spread over the runners that ran):")
rules(R["stale"][:, 3], "the same races re-priced on the final field (replay, stale history):")
rules(R["fresh"][:, 3], "re-priced on the final field with fresh history:")
