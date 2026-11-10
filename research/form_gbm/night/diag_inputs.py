import collections, json, sys
import numpy as np
sys.path.insert(0, "/home/user/fk-model/research/form_gbm")
import track_rules as tr
Z = np.load("ds/model_ds.npz", allow_pickle=True); R = np.load("replay_stale.npz"); LJ = np.load("live_join.npz")
ri = Z["race_idx"]; nR = len(Z["race_id"]); rdate = Z["date"].astype(str); date = rdate[ri]
cols = list(Z["cols"]); bar = Z["X"][:, cols.index("barrier")]; jk = Z["jockey"].astype(str)
print("pre_jump races in the dataset:", int(Z["pre_jump"].sum()), "of", nR, "; from 15 Oct:", int(Z["pre_jump"][rdate > "2026-10-14"].sum()), "of", int((rdate > "2026-10-14").sum()))
key = {(str(Z["race_id"][ri[i]]), str(Z["horse_id"][i])): i for i in np.where(date > "2026-10-14")[0]}
nfile = collections.Counter(); fj = {}; fb = {}; tagof = {}; when = {}
for pre, (ts, tag, f) in sorted(tr.model_files().items()):
    if pre[:10] <= "2026-10-14": continue
    for r in json.load(open(f)):
        nfile[r["race_id"]] += 1
        i = key.get((r["race_id"], r["horse_id"]))
        if i is not None: fj[i] = r.get("jockey", ""); fb[i] = r.get("barrier"); when[i] = (ts, pre[:10])
nran = np.bincount(ri, minlength=nR)
d = np.abs(np.log(LJ["p_trees"] / R["stale"][:, 0])); ok = np.isfinite(d)
late = np.array([nfile.get(str(Z["race_id"][r]), 0) - nran[r] for r in range(nR)])[ri]
jchg = np.array([fj.get(i, jk[i]).strip().lower() != jk[i].strip().lower() for i in range(len(ri))])
bchg = np.array([(fb.get(i) is not None) and np.isfinite(bar[i]) and int(fb[i]) != int(bar[i]) for i in range(len(ri))])
racej = np.bincount(ri, weights=jchg & ok, minlength=nR)[ri] > 0; raceb = np.bincount(ri, weights=bchg & ok, minlength=nR)[ri] > 0
def show(lab, m):
    m = m & ok
    if not m.sum(): print(f"  {lab:58s}     0 runners"); return
    print(f"  {lab:58s} {int(m.sum()):5d} runners  median {100*np.median(d[m]):4.1f}%  90th {100*np.percentile(d[m],90):5.1f}%  over 10%: {100*np.mean(d[m]>0.0953):3.0f}%")
print("live trees v stale-replay trees (same model, same history), by what changed between pricing and the race:")
show("all", ok)
show("race had late scratchings after the file was made", late > 0)
show("no late scratching", late == 0)
show("no late scratching, a jockey changed in the race", (late == 0) & racej)
show("no late scratching, a barrier differs in the race", (late == 0) & raceb)
show("no late scratching, no jockey or barrier change in the race", (late == 0) & ~racej & ~raceb)
print("  runners whose own jockey changed:", int((jchg & ok).sum()), " own barrier differs:", int((bchg & ok).sum()))
# same-day files (priced on race morning) v files priced a day or more before
sameday = np.array([when[i][0][:10] >= when[i][1] if i in when else False for i in range(len(ri))])
show("file committed on race day (the 9:30 re-price)", sameday); show("file committed before race day", ~sameday & ok)
clean = (late == 0) & ~racej & ~raceb & ok
np.save("clean_mask.npy", clean)

# KL and log loss, live trees v rebuilt-input trees, by race group (whole races)
bs = Z["bsp"].astype(float); won = Z["finish"] == 1
okb = np.isfinite(bs) & (bs > 1); inv = np.where(okb, 1 / np.where(okb, bs, 2), 0); q = inv / np.maximum(np.bincount(ri, weights=inv, minlength=nR)[ri], 1e-12)
qfull = (np.bincount(ri, weights=~okb, minlength=nR) == 0) & (np.bincount(ri, weights=won, minlength=nR) == 1)
racefull = np.bincount(ri, weights=~ok, minlength=nR) == 0
def klll(p, rm):
    g = rm[ri] & qfull[ri] & racefull[ri]; n = len(np.unique(ri[g]))
    kl = np.sum(q[g] * np.log(np.maximum(q[g], 1e-300) / np.maximum(p[g], 1e-12))) / max(n, 1)
    llr = -np.log(np.maximum(p[g & won], 1e-12)); return kl, llr.mean(), n, llr
rlate = np.bincount(ri, weights=(late > 0), minlength=nR) > 0; rj = np.bincount(ri, weights=jchg & ok, minlength=nR) > 0
live_r = (rdate > "2026-10-14")
print("\n| races | n | live file trees KL | rebuilt-input trees KL | live log loss | rebuilt log loss | paired diff (SE) |\n|---|---|---|---|---|---|---|")
for lab, rm in (("all", live_r), ("late scratching after pricing", live_r & rlate), ("no late scratching, a jockey changed", live_r & ~rlate & rj),
                ("clean: same field, same jockeys", live_r & ~rlate & ~rj)):
    a = klll(LJ["p_trees"], rm); b_ = klll(R["stale"][:, 0], rm); dd = a[3] - b_[3]
    print(f"| {lab} | {a[2]} | {a[0]:.4f} | {b_[0]:.4f} | {a[1]:.4f} | {b_[1]:.4f} | {dd.mean():+.4f} ({dd.std(ddof=1)/np.sqrt(len(dd)):.4f}) |")
# the stage-2 price too
print("\nstage 2 (our price before the open blend), the same groups:")
for lab, rm in (("all", live_r), ("late scratching after pricing", live_r & rlate), ("no late scratching, a jockey changed", live_r & ~rlate & rj),
                ("clean: same field, same jockeys", live_r & ~rlate & ~rj)):
    a = klll(LJ["p_model"], rm); b_ = klll(R["stale"][:, 3], rm); dd = a[3] - b_[3]
    print(f"| {lab} | {a[2]} | {a[0]:.4f} | {b_[0]:.4f} | {a[1]:.4f} | {b_[1]:.4f} | {dd.mean():+.4f} ({dd.std(ddof=1)/np.sqrt(len(dd)):.4f}) |")
# what did the jockey change look like: undeclared at pricing, or a real switch?
und = sum(1 for i in np.where(jchg & ok)[0] if not fj.get(i, "").strip())
print(f"\nrunners whose jockey differs from the file: {int((jchg & ok).sum())}; of those, no rider declared when priced: {und}")

print("\nBefore and after the 1 Nov rider fix (stage 2, live file v rebuilt inputs):")
for lab, lo, hi in (("15-31 Oct", "2026-10-15", "2026-11-01"), ("1-9 Nov", "2026-11-01", "2026-11-10")):
    per = (rdate >= lo) & (rdate < hi)
    for g, rm in (("all", per), ("late scratching", per & rlate), ("rider missing/changed", per & ~rlate & rj), ("clean", per & ~rlate & ~rj)):
        a = klll(LJ["p_model"], rm); b_ = klll(R["stale"][:, 3], rm); c = klll(R["fresh"][:, 3], rm)
        if a[2]: print(f"  {lab} {g:22s} {a[2]:3d} races  live {a[0]:.4f}  rebuilt-stale {b_[0]:.4f}  rebuilt-fresh {c[0]:.4f}   log loss {a[1]:.4f} / {b_[1]:.4f} / {c[1]:.4f}")
