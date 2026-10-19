"""Audit of every live no-bet block in the BetMatic order pipeline (19 Oct 2026). Read-only research.

Holdout = races from 2026-06-03 (v10_profit_preds.npz `hold`), our chance = p10 (v10 trees trained before 3 Jun).
Order rule as betmatic_orders.py / t_v10_profit.run(): E = 1.2 (1.15 when the open is under $4), min odds
0.95 x (E / p^0.82)^(1/0.78) rounded to the cent, steps x1/x1.25/x1.5 under the ceiling (3x our price, or $8 for an
EARLY tag), each step sized at the NEXT step's price on stake_rule.stake(p^0.82 t^-0.22, t) (5u cap), fired when the
open reaches the step. Our price $1.60-$15. Settled at the open with a 16% deduction on winnings, and at BSP less 8%.

Blocks re-implemented from the dataset columns exactly as the live scripts compute them:
  bounce      fu_json.py in the LIVE model dir (the repo copy removed it on 13 Oct; the model dir copy still has it,
              and the live first-up-blocks.json files through 21 Oct still carry "bounce:" reasons):
              last real start rating >= best of the earlier real starts in the 10-row history + 3
  first-up    last real start 60+ days ago AND (200m+ shorter today than that start, OR the most recent trial since
              that start finished in the bottom half: (fin-1)/(runners-1) > 0.5)
  early $8    second-up after a first-up (prep==1 at last start) that finished top 3 or within 2L: ceiling $8
              (only when no block reason; the gap must be < 60 days or the gap>=60 branch found no reason)
  first starter  X[firstStarter] == 1 (fs_json.py)
  race FS rule   no bets in a race where a first starter opens $6 or shorter (race_check.py / fwd_betmatic.py;
                 NOT in the pre-open order file, it needs the market)
Each block is scored as a marginal counterfactual: the bets that would exist if that one block were lifted and every
other block stayed in force. Bootstrap by race (2,000 draws) for the standard error of the profit.

    python3.13 t_blocks_audit.py"""
import numpy as np, stake_rule

D = np.load("ds/model_ds_v10.npz", allow_pickle=True)
V = np.load("v10_profit_preds.npz")
ri = D["race_idx"]; nR = int(ri.max()) + 1; n = len(ri); ar = np.arange(n)
pm = V["p10"].astype(float); hm = V["hold"].astype(bool)
o = D["open"].astype(float); bs = D["bsp"].astype(float); won = D["finish"].astype(float) == 1
okp = np.isfinite(o) & (o > 1); race_ok = np.bincount(ri, weights=~okp, minlength=nR) == 0
base = hm & race_ok[ri] & np.isfinite(bs) & (bs > 1) & (pm > 0)
DED, BSP_COMM, TIERS, SHADE = 0.16, 0.08, (1.0, 1.25, 1.5), 0.95

# ---------- block conditions (fu_json.py / fs_json.py, model-dir copy) ----------
P = D["P"].astype(float); f = {str(x): i for i, x in enumerate(D["past_fields"])}
g = lambda k: P[:, :, f[k]]
tr = g("trial") == 1; fin = g("finish"); days = g("days_before"); run = g("runners"); dist = g("distance")
rat = g("rating"); mg = g("margin"); prep = g("prep")
real = ~tr & np.isfinite(fin) & (fin > 0)
has = real.any(1); j = np.argmax(real, 1)
nreal = real.sum(1)
lv = lambda a: np.where(has, a[ar, j], np.nan)
gap = lv(days)
# bounce: rat[j] >= nanmax(rat over the earlier real starts) + 3
prior = np.where(real, rat, np.nan); prior[ar, j] = np.nan
with np.errstate(all="ignore"):
    best = np.nanmax(np.where(np.arange(10)[None, :] > j[:, None], prior, np.nan), 1)
bounce = has & (nreal > 1) & np.isfinite(lv(rat)) & np.isfinite(best) & (lv(rat) >= best + 3)
# first-up reasons (only when gap >= 60)
drop = lv(dist) - D["distance"][ri].astype(float)
tri = tr & np.isfinite(fin) & (fin > 0) & (days < gap[:, None]); tj = np.argmax(tri, 1); hast = tri[ar, tj]
trel = np.where(hast, (fin[ar, tj] - 1) / np.maximum(run[ar, tj] - 1, 1), np.nan)
fu60 = has & (gap >= 60)
fu_short = fu60 & (drop >= 200); fu_trial = fu60 & hast & (trel > 0.5)
firstup = fu_short | fu_trial
early = has & (lv(prep) == 1) & ((lv(fin) <= 3) | (np.isfinite(lv(mg)) & (lv(mg) <= 2)))
cols = list(D["cols"]); fs = D["X"][:, cols.index("firstStarter")] == 1
fs_short = np.bincount(ri, weights=(fs & okp & (o <= 6)).astype(float), minlength=nR)[ri] > 0

# ---------- the order rule ----------
def stake_at_open(i, cap):
    p = pm[i]; q = 1 / p; oo = o[i]
    if not (1.6 <= q <= 15) or not oo < cap:
        return 0.0
    E = 1.15 if oo < 4 else 1.2
    mo = round(SHADE * (E / p ** 0.82) ** (1 / 0.78), 2)
    if oo < mo:
        return 0.0
    ts = [round(mo * s, 2) for s in TIERS if mo * s < cap]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if oo >= t:
            tot += add
    return tot

def stakes(blocks):
    """Stake per runner with the named blocks in force (a set of 'bounce','firstup','early','fs','fsrace')."""
    st = np.zeros(n)
    for i in np.where(base)[0]:
        if "fs" in blocks and fs[i]: continue
        if "fsrace" in blocks and fs_short[i]: continue
        reason = ("bounce" in blocks and bounce[i]) or ("firstup" in blocks and firstup[i])
        if reason: continue
        # EARLY tag only when fu_json found no reason (with bounce lifted, a bounce horse can become EARLY)
        cap = 3 / pm[i]
        if "early" in blocks and early[i]: cap = min(cap, 8.0)
        st[i] = stake_at_open(i, cap)
    return st

pl_open = lambda st: np.where(won, st * (o - 1) * (1 - DED), -st)
pl_bsp = lambda st: np.where(won, st * (bs - 1) * (1 - BSP_COMM), -st)
rng = np.random.default_rng(1)

def boot(pl, mask):
    races = np.unique(ri[mask]);
    if not len(races): return np.nan, np.nan
    tot = np.bincount(ri, weights=np.where(mask, pl, 0), minlength=nR)[races]
    b = np.array([tot[rng.integers(0, len(races), len(races))].sum() for _ in range(2000)])
    return b.std(), (b <= 0).mean()

def row(label, st, mask):
    m = mask & (np.abs(st) > 1e-12); s = st[m].sum(); po = pl_open(st)[m].sum(); pb = pl_bsp(st)[m].sum()
    se, pneg = boot(pl_open(st), m)
    return (f"| {label} | {m.sum()} | {int(won[m].sum())} | {s:.1f}u | {po:+.1f}u ({po/s if s else 0:+.0%}) "
            f"| {se:.0f}u | {pneg:.2f} | {pb:+.1f}u ({pb/s if s else 0:+.0%}) |")

def calib(label, mask):
    m = mask & base; w = won[m].sum(); e = pm[m].sum(); sd = np.sqrt((pm[m] * (1 - pm[m])).sum())
    inv = np.where(np.isfinite(bs) & (bs > 1), 1 / bs, 0); qb = inv / np.bincount(ri, weights=inv, minlength=nR)[ri]
    io = np.where(okp, 1 / o, 0); qo = io / np.bincount(ri, weights=io, minlength=nR)[ri]
    return (f"| {label} | {m.sum()} | {int(w)} | {e:.1f} | {(w-e)/sd if sd else 0:+.1f} | {qo[m].sum():.1f} | {qb[m].sum():.1f} |")

ALL = {"bounce", "firstup", "early", "fs", "fsrace"}
live = stakes(ALL)
print(f"holdout races from 2026-06-03 with every open: {len(np.unique(ri[base]))}; runners {base.sum()}")
print(f"blocked runners in the holdout base: bounce {(bounce&base).sum()}, first-up {(firstup&base).sum()} "
      f"(short {(fu_short&base).sum()}, poor trial {(fu_trial&base).sum()}), early-tag {(early&base).sum()}, "
      f"first starters {(fs&base).sum()}, in a FS<=$6 race {(fs_short&base).sum()}\n")
print("| bets | n | won | staked | profit at open (ROI) | boot SE | P(profit<=0) | profit at BSP (ROI) |\n|---|---|---|---|---|---|---|---|")
print(row("LIVE: all blocks in force (kept bets)", live, base))
print(row("no blocks at all", stakes(set()), base))
print(row("live minus bounce (repo version, bounce lifted)", stakes(ALL - {"bounce"}), base))
for b, lab in (("bounce", "bounce"), ("firstup", "first-up"), ("early", "EARLY $8 cap"), ("fs", "first starters"), ("fsrace", "race FS<=$6 rule")):
    st = stakes(ALL - {b}); d = st - live
    add = d > 1e-9; cut = d < -1e-9
    print(row(f"ADDED by lifting {lab}", d, add))
    if cut.any(): print(row(f"  (stake reduced by lifting {lab})", d, cut))
# split first-up into its two reasons, as added bets
for lab, cond in (("first-up: 200m+ short only", fu_short & ~fu_trial), ("first-up: poor trial only", fu_trial & ~fu_short), ("first-up: both", fu_short & fu_trial)):
    st = stakes(ALL - {"firstup"}); d = np.where(cond, st - live, 0)
    print(row(f"ADDED by lifting {lab}", d, d > 1e-9))
# bounce by gap
st = stakes(ALL - {"bounce"}); d = st - live
for lab, cond in (("bounce, back within 21 days", gap <= 21), ("bounce, 22+ days", gap > 21)):
    dd = np.where(cond, d, 0); print(row(f"ADDED by lifting {lab}", dd, dd > 1e-9))
# halves of the holdout for the two removable-looking ones
mid = "2026-08-10"; newer = (D["date"][ri] >= mid)
for b, lab in (("bounce", "bounce"), ("firstup", "first-up"), ("early", "EARLY $8 cap"), ("fs", "first starters"), ("fsrace", "race FS rule")):
    d = stakes(ALL - {b}) - live
    print(row(f"{lab} added, before {mid}", d, (d > 1e-9) & ~newer)); print(row(f"{lab} added, from {mid}", d, (d > 1e-9) & newer))

print("\nCalibration: winners vs our model's expected (sum p10); z = (won - sum p) / sd; market sums for reference")
print("| group | runners | won | sum p10 | z | sum open chance | sum BSP chance |\n|---|---|---|---|---|---|---|")
print(calib("all holdout runners", np.ones(n, bool)))
print(calib("bounce runners", bounce)); print(calib("first-up blocked", firstup))
print(calib("  200m+ short", fu_short)); print(calib("  poor trial", fu_trial))
print(calib("early-tag runners", early)); print(calib("first starters", fs)); print(calib("runners in a FS<=$6 race (non-FS)", fs_short & ~fs))
for b, lab in (("bounce", "bounce"), ("firstup", "first-up"), ("early", "EARLY $8"), ("fs", "first starters"), ("fsrace", "race FS rule")):
    d = stakes(ALL - {b}) - live; print(calib(f"  {lab}: the would-be bets", d > 1e-9))
print(calib("LIVE kept bets", live > 0))
