"""Does the 9:30 re-price beat the first price? (night of 10 Nov 2026). Every live meeting has its first model file
(priced when the fields came out, a day or two before) and its last (the race-morning re-price on the final field with
riders in). Both against BSP on the same races, renormalised over the runners that ran.
    python3.13 first_vs_last.py   (replay folder)"""
import collections, glob, json, os, subprocess, sys
import numpy as np
L = "/home/user/fk-model/data/live_bets"; REPO = "/home/user/fk-model"
Z = np.load("ds/model_ds.npz", allow_pickle=True); ri = Z["race_idx"]; nR = len(Z["race_id"]); rdate = Z["date"].astype(str)
bs = Z["bsp"].astype(float); won = Z["finish"] == 1
okb = np.isfinite(bs) & (bs > 1); inv = np.where(okb, 1 / np.where(okb, bs, 2), 0); q = inv / np.maximum(np.bincount(ri, weights=inv, minlength=nR)[ri], 1e-12)
qfull = (np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
key = {(str(Z["race_id"][ri[i]]), str(Z["horse_id"][i])): i for i in range(len(ri)) if rdate[ri[i]] >= "2026-10-09"}
files = collections.defaultdict(list)
for f in glob.glob(f"{L}/2026-1*-v6.json"):
    b = os.path.basename(f); pre, tag = b[:-8].rsplit("-", 1)
    ts = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--", f], capture_output=True, text=True, cwd=REPO).stdout.strip().split("\n")[-1]
    if ts: files[pre].append((ts, tag, f))
def load(f, field="p_model"):
    p = np.full(len(ri), np.nan); n = collections.Counter(); nj = 0
    for r in json.load(open(f)):
        n[r["race_id"]] += 1; i = key.get((r.get("race_id"), r.get("horse_id")))
        if i is not None: p[i] = r.get(field, r["p"]); nj += (not str(r.get("jockey", "")).strip())
    v = np.where(np.isfinite(p), p, 0); tot = np.bincount(ri, weights=v, minlength=nR); full = np.bincount(ri, weights=~np.isfinite(p), minlength=nR) == 0
    return np.where(full[ri] & (tot[ri] > 0), v / np.maximum(tot[ri], 1e-12), np.nan), full, n
A = np.full(len(ri), np.nan); B = np.full(len(ri), np.nan); gap_h = []; used = 0
for pre, lst in sorted(files.items()):
    day = pre[:10]; lst = sorted(x for x in lst if x[0][:10] <= day)      # committed up to race day (UTC)
    if len(lst) < 2: continue
    first, last = lst[0], lst[-1]
    hrs = (np.datetime64(last[0][:19]) - np.datetime64(first[0][:19])).astype("timedelta64[h]").astype(int)
    if hrs < 6: continue
    pa, fa, _ = load(first[2]); pb, fb, _ = load(last[2]); m = np.isfinite(pa) & np.isfinite(pb)
    if m.any(): A[m] = pa[m]; B[m] = pb[m]; used += 1; gap_h.append(hrs)
m = np.isfinite(A) & np.isfinite(B) & qfull[ri]; races = len(np.unique(ri[m]))
kl = lambda p: np.sum(np.where(q[m] > 0, q[m] * np.log(np.maximum(q[m], 1e-300) / np.maximum(p[m], 1e-12)), 0)) / races
ll = lambda p: -np.mean(np.log(np.maximum(p[m & won], 1e-12)))
print(f"{used} meetings with a first price and a later re-price 6+ hours apart (median {int(np.median(gap_h))} hours); {races} races priced by both")
print(f"  first price:  KL to BSP {kl(A):.4f}, winner log loss {ll(A):.4f}")
print(f"  last price:   KL to BSP {kl(B):.4f}, winner log loss {ll(B):.4f}")
d = np.abs(np.log(B[m] / A[m])); print(f"  runner by runner the two are a median {100*np.median(d):.1f}% apart; over 10% apart {100*np.mean(d > 0.0953):.0f}%")
kr = lambda p: np.bincount(ri[m], weights=np.where(q[m] > 0, q[m] * np.log(np.maximum(q[m], 1e-300) / np.maximum(p[m], 1e-12)), 0), minlength=nR)
dd = (kr(A) - kr(B))[np.unique(ri[m])]; print(f"  paired gain of the re-price: {dd.mean():+.4f} a race (SE {dd.std(ddof=1)/np.sqrt(len(dd)):.4f}); closer in {100*np.mean(dd > 0):.0f}% of races")
