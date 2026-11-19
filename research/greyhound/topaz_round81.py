"""Round 81: the order sheet as BetMatic bands, each with a ceiling and its own stake (19 Nov 2026, after Test 100)

Test 100 (round 80) set each dog's minimum TAB price before the open and fired at any price at or above it. Flat, it
lost (-4.1% to -0.3% a unit by the corrected BSP): most of the dogs it backed alone, the best model knowing TAB's
whole opening book would not have backed, and those lost about 15% a unit. A quarter of Kelly, staked by the edge at
TAB's actual price, made +280 to +383 corrected BSP units: the edge was there, but only where the model still saw one
at the price TAB opened. A minimum alone cannot say that, and a fixed stake cannot follow the edge. A BetMatic order
carries a minimum AND a maximum price (the gallops order files have used max_odds since 14 Oct 2026), so a dog can
carry several orders, one a price band, each with its own stake.

Stated before the run. The same best model and the same predicted fields as Test 100 (round 80's walk, read back), for
every runner from February 2025:

  - each dog's chance on a 28-point ladder of its own TAB price, $1.15 to $41 (each step about 14%), the rest of the
    field predicted three ways as in Test 100 (ours scaled to TAB's usual book; the TAB-open model; the TAB-open model
    with the rest not moving)
  - a band is the price range between two neighbouring ladder prices. The dog gets an order on a band when the best
    model's rule holds at BOTH its ends (its chance at least the margin over 1 / price, its fair price under $15).
    Flat, the order's stake is one unit. At a quarter of Kelly, it is the smaller of the quarter-Kelly stakes at the
    band's two ends, on Test 98's scale. Neighbouring flat bands are one order (BetMatic's minimum and maximum)
  - the order fires when TAB's first price falls in its band and is paid TAB's first price after its deduction (a
    deduction is not known before the open, so the stake and the rule use the price before it)
  - the margin over 1 / price at 2, 4, 6 and 8 points, because the field's prediction misses TAB's price by about
    a quarter and a wider margin may keep only the bets the miss cannot undo
  - as the most a band sheet could do: the same rule and stake at TAB's actual first price (bands infinitely fine)
  - judged beside the best model on TAB's whole opening book (Test 98's bets, the most a reaction could do): flat and
    at a quarter of Kelly, by half and by three months; the bets both make and each alone; how many orders a dog needs

Saved as corr_r81 (race_id, dog, and each field's chance at TAB's actual first price) in the walk cache.

    ROUND80_REUSE=yes python research/greyhound/topaz_round81.py DIR LABEL    (round 80's walk in the walk cache)

Counts, sums and rates only: no race, dog or price is printed. The model's inputs are named.
"""
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import topaz_round63 as R63       # noqa: E402
import topaz_round58 as R58       # noqa: E402
import topaz_round67 as R67       # noqa: E402
import topaz_round68 as R68       # noqa: E402
import topaz_round70 as R70       # noqa: E402
import topaz_round73 as R73       # noqa: E402
import topaz_round79 as R79       # noqa: E402
import topaz_round80 as R80       # noqa: E402

TAG = "r81"
FAIR_UNDER = R80.FAIR_UNDER
GRID = np.geomspace(1.15, 41.0, 28)
MARGINS = (0.02, 0.04, 0.06, 0.08)
NAMES = R80.NAMES


def ladder_rule(pg: np.ndarray, grid: np.ndarray, d: float) -> np.ndarray:
    """The best model's rule at each ladder price (runners x prices): its chance at least d over 1 / price, its fair
    price under $15."""
    g = np.asarray(grid, float)[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.isfinite(pg) & (pg > 0) & (pg - 1 / g >= d - 1e-12) & (1 / pg < FAIR_UNDER)


def rule_at(p: np.ndarray, price: np.ndarray, d: float) -> np.ndarray:
    """The same rule at one price a runner: its chance at least d over 1 / price, its fair price under $15."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.isfinite(p) & (p > 0) & np.isfinite(price) & (p - 1 / price >= d - 1e-12) & (1 / p < FAIR_UNDER)


def band_orders(pg: np.ndarray, grid: np.ndarray, d: float, scale: float) -> tuple:
    """Each runner's orders on the bands between neighbouring ladder prices: (valid, runners x bands: the rule holds at
    both ends; the quarter-Kelly stake on each, the smaller of its two ends', 0 where not valid)."""
    ok = ladder_rule(pg, grid, d)
    valid = ok[:, :-1] & ok[:, 1:]
    k = R73.raw_kelly(pg, np.asarray(grid, float)[None, :]) / scale
    ks = np.minimum(k[:, :-1], k[:, 1:])
    return valid, np.where(valid, ks, 0.0)


def band_of(price: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """The band each price falls in (grid[j] <= price < grid[j + 1]), -1 outside the ladder."""
    p = np.asarray(price, float)
    j = np.searchsorted(np.asarray(grid, float), np.nan_to_num(p, nan=-1.0), side="right") - 1
    return np.where(np.isfinite(p) & (j >= 0) & (j < len(grid) - 1), j, -1)


def fire(valid: np.ndarray, ks: np.ndarray, j: np.ndarray) -> tuple:
    """(fired: the runner has an order on the band its TAB price fell in; that order's quarter-Kelly stake)."""
    rows = np.arange(len(j))
    jj = np.maximum(j, 0)
    hit = (j >= 0) & valid[rows, jj]
    return hit, np.where(hit, ks[rows, jj], 0.0)


def orders_flat(valid: np.ndarray) -> np.ndarray:
    """BetMatic orders each runner needs flat: one per run of neighbouring valid bands (a minimum and a maximum)."""
    v = valid.astype(bool)
    if not v.shape[1]:
        return np.zeros(len(v), int)
    return v[:, 0].astype(int) + (v[:, 1:] & ~v[:, :-1]).sum(axis=1)


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 81, the order sheet as BetMatic bands\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    keep, drop = R79.live_inputs(inputs)
    XK = XR[keep]
    has70 = R67.read_saved(x, "r70", "c_f")
    has79 = R67.read_saved(x, "r79", "c_v")
    print(f"Inputs known on the morning: {len(keep)} (dropped as BSP-based: {len(drop)}). Test 88's fit "
          f"{'is' if has70 else 'is NOT'} in the walk cache, Test 98's {'is' if has79 else 'is NOT'}. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.\n")

    p, log, models = R80.walk_kept(R, XK, q, use, off_tab)
    print("## 1. Test 98's walk, with each refit's model\n\n" + "; ".join(log[-2:]) + "\n")
    race, dates = R.race_id.values, R.date.values.astype("datetime64[ns]")
    ran = x.is_ran.astype(bool).values
    t = x[ran].reset_index(drop=True)
    to_t = np.full(len(x), -1)
    to_t[np.flatnonzero(ran)] = np.arange(int(ran.sum()))
    tpos = to_t[R["index"].values]

    def on_t(a):
        a = np.asarray(a)
        out = np.full((len(t),) + a.shape[1:], np.nan)
        out[tpos] = a
        return out

    if has79:
        pv = R70.on_runners(R, t, "c_v")
        both = np.isfinite(p) & np.isfinite(pv)
        print(f"Against Test 98's saved walk: {int(both.sum()):,} runners, mean difference "
              f"{np.mean(np.abs(p[both] - pv[both])):.5f} in chance\n")

    since_r = dates >= np.datetime64(R63.SINCE)
    book = R80.usual_book(R)
    nb = R.n_bet.values.astype(float)
    nl = np.clip(nb - pd.Series(np.ones(len(R))).groupby(race).transform("sum").values, 0, None)
    later_pred = book * nl / nb
    ran_book = book * (1 - nl / nb)
    inv_ours = ran_book * np.exp(XK.lp_ours.values.astype(float))
    pred, plog = R80.walk_tab_open(R, XK)
    inv_model = ran_book * R80.race_share(pred, race)
    print(f"## 2. The rest of the field before the open ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    print("| prediction of each runner's TAB first price | how close, February 2025 on |\n|---|---|")
    inv_act = 1 / R.price.values.astype(float)
    for nm, v in (("ours, scaled to TAB's usual book", inv_ours), ("the TAB-open model", inv_model)):
        print(f"| {nm} | {R80.errors(v, inv_act, since_r)} |")

    lp_ours = XK.lp_ours.values.astype(float)
    month = pd.Series(R.date.values).dt.to_period("M").array
    price_r = R.price.values.astype(float)
    K = len(GRID)
    res = {nm: (np.full((len(R), K), np.nan), np.full(len(R), np.nan)) for nm, _ in NAMES}
    for i, (M, bst) in enumerate(models):
        nxt = models[i + 1][0] if i + 1 < len(models) else None
        blk = np.flatnonzero(since_r & (month >= M) & ((month < nxt) if nxt is not None else True) & np.isfinite(p))
        if not len(blk) or bst is None:
            continue
        pf = (lambda X, b=bst: b.predict(X, raw_score=True))
        for nm, inv_o, hold in R80.VARIANTS(inv_ours, inv_model):
            gap_races = pd.unique(race[blk][~np.isfinite(inv_o[blk]) | ~np.isfinite(later_pred[blk])])
            rows = blk[~np.isin(race[blk], gap_races)]           # a race is priced whole or not at all
            if not len(rows):
                continue
            sh = R80.Sheet(XK.iloc[rows], lp_ours[rows], inv_o[rows], later_pred[rows], race[rows], pf, hold_book=hold)
            n = len(rows)
            res[nm][0][rows] = np.column_stack([sh.chance(np.full(n, g)) for g in GRID])
            res[nm][1][rows] = sh.chance(price_r[rows])
        print(f"{M}: {len(blk):,} runners priced on the ladder, {(time.monotonic() - t0) / 60:.0f} minutes in")

    cdir = os.environ.get("WALK_CACHE_DIR", "")
    if cdir:
        Path(cdir).mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"race_id": R.race_id.values, "dog": R.dog.values,
                      **{f"p_{nm}": res[nm][1] for nm, _ in NAMES}}).to_csv(
            Path(cdir) / f"corr_{TAG}.csv.gz", index=False, float_format="%.6g")

    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    price = t.price.values.astype(float)
    since = R63.R36.in_period(t, R63.SINCE, None)
    pm = on_t(p)
    m98 = R68.margin_bets(t, pm, R80.MARGIN)
    base = R67.model_chance(t, "c_f") if has70 else pm
    scale = R73.raw_kelly(base, paid)[R68.margin_bets(t, base, R80.MARGIN) & since].mean()
    u98 = R73.raw_kelly(pm, paid) / scale
    m98 &= u98 > 0
    flat = np.ones(len(t))
    jt = band_of(price, GRID)
    rules = {"the best model on TAB's whole opening book (Test 98)": dict(fm=m98 & since, km=m98 & since, uk=u98)}
    extra = {}
    for nm, lab in NAMES:
        pg, pa = on_t(res[nm][0]), on_t(res[nm][1])
        for dm in MARGINS:
            ok_a = rule_at(pa, price, dm) & since
            uk_a = R73.raw_kelly(pa, price) / scale
            rules[f"{lab}, {dm * 100:.0f} points, at TAB's actual price"] = dict(fm=ok_a, km=ok_a & (uk_a > 0), uk=uk_a)
            valid, ks = band_orders(pg, GRID, dm, scale)
            hit, uk_b = fire(valid, ks, jt)
            hit &= since
            key = f"{lab}, {dm * 100:.0f} points, bands"
            rules[key] = dict(fm=hit, km=hit & (uk_b > 0), uk=uk_b)
            has = valid.any(axis=1) & since
            extra[key] = dict(set=has, flat_orders=orders_flat(valid)[has], kelly_orders=valid.sum(axis=1)[has],
                              hit=hit)

    print(f"\n## 3. Every rule, February 2025 on ({(time.monotonic() - t0) / 60:.0f} minutes in; the quarter Kelly "
          f"on Test 98's scale, {scale:.4f})\n")
    print("| rule | flat: bets | flat: corrected BSP per unit (SE) | flat: corrected BSP units | flat: realised | "
          "quarter Kelly: bets | units staked | corrected BSP per unit (SE) | corrected BSP units | realised | luck (SD) "
          "| deepest fall | losing months |\n|" + "---|" * 13)
    for nm, r in rules.items():
        s = R68.staked(tq, r["fm"], paid, flat)
        fcell = (f"{s['n']:,} | {s['per']:+.1%} ({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f}"
                 if s["n"] else "0 | | |")
        print(f"| {nm} | {fcell} | " + R73.kelly_row(t, tq, r["km"], paid, r["uk"]) + " |")

    print("\n## 4. By half: corrected BSP units / realised units, flat and at a quarter of Kelly\n")
    print("| rule | " + " | ".join(f"{h[0]}, flat | {h[0]}, quarter Kelly" for h in R63.HALVES) + " |\n|"
          + "---|" * (1 + 2 * len(R63.HALVES)))
    for nm, r in rules.items():
        if "actual price" in nm:
            continue
        cells = []
        for _, lo, hi in R63.HALVES:
            per = R63.R36.in_period(t, lo, hi)
            for mk, u in ((r["fm"], flat), (r["km"], r["uk"])):
                s = R68.staked(tq, mk & per, paid, u)
                cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "none")
        print(f"| {nm} | " + " | ".join(cells) + " |")

    print("\n## 5. The band sheet's orders, February 2025 on\n")
    print("| rule | dogs given an order | BetMatic orders a dog, flat (median, most) | orders a dog, quarter Kelly (one a "
          "band: median, most) | fired | bets Test 98 makes too | Test 98's bets the sheet misses |\n|" + "---|" * 7)
    for nm, e in extra.items():
        fo, ko = e["flat_orders"], e["kelly_orders"]
        print(f"| {nm} | {int(e['set'].sum()):,} | {np.median(fo) if len(fo) else 0:.0f}, {fo.max() if len(fo) else 0} "
              f"| {np.median(ko) if len(ko) else 0:.0f}, {ko.max() if len(ko) else 0} | {int(e['hit'].sum()):,} | "
              f"{int((e['hit'] & m98 & since).sum()):,} | {int((m98 & since & ~e['hit']).sum()):,} |")

    print("\n## 6. At a quarter of Kelly, by who makes the bet (corrected BSP units / realised units, bets)\n")
    print("| rule | both | the sheet only | Test 98 only |\n|---|---|---|---|")
    for nm in extra:
        r = rules[nm]
        cells = []
        for mk, u in ((r["km"] & m98, r["uk"]), (r["km"] & ~m98, r["uk"]), (m98 & since & ~r["km"], u98)):
            s = R68.staked(tq, mk, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f} ({s['n']:,})" if s["n"] else "none")
        print(f"| {nm} | " + " | ".join(cells) + " |")

    shown = [k for k in rules if "Test 98" in k] + [k for k in extra if " 2 points" in k or " 4 points" in k]
    print("\n## 7. By three months, a quarter of Kelly: corrected BSP units / realised units\n")
    print("| three months | " + " | ".join(shown) + " |\n|" + "---|" * (len(shown) + 1))
    for bname, lo, hi in R68.blocks(R63.SINCE, None):
        per = R63.R36.in_period(t, lo, hi)
        cells = []
        for k in shown:
            s = R68.staked(tq, rules[k]["km"] & per, paid, rules[k]["uk"])
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f}" if s["n"] else "no BSP yet")
        print(f"| {bname} | " + " | ".join(cells) + " |")
    print(f"\n{(time.monotonic() - t0) / 60:.0f} minutes")
    return 0


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 81")
