"""Round 82: round 81's band sheet on Test 98's footing for dogs scratched after the open (19 Nov 2026)

Round 81 (Test 101 as first run) set BetMatic band orders from the best model's chance on a ladder of each dog's TAB
price. Its chance is over the runners that RAN, but its rule and stake read TAB's price BEFORE TAB's deduction for the
dogs scratched after the open. That pair does not match:
  - Test 98 compares the same chance (over the runners that ran) with 1 / the price paid AFTER the deduction. Both
    halves know the scratching, and TAB's deduction is set to roughly undo the scratched dog's share, so the pair is
    close to what a bettor at the open sees (the field at the bet, at TAB's price as shown).
  - Round 81 compares the chance that knows the scratching with the price that does not. In a race where a dog was
    scratched after the open, every dog's chance is inflated by the scratched dog's share while its price is not cut,
    so the rule sees an edge that is not there, takes the bet, and is paid the cut price. Round 80's minimum did the
    same.
So round 81 judged the band sheet on a harder footing than Test 98 in the races with a scratching after the open.

Stated before the run. Everything as round 81 (the same walk, fields, 28-point ladder, margins and stakes), except:

  - at each ladder price g, the rule and the quarter-Kelly stake read the price paid at g, 1 + (g - 1) x (1 - TAB's
    deduction), as Test 98 does (the order still fires on TAB's price as shown, which is what BetMatic sees)
  - the same at TAB's actual price (the most a band sheet could do)
  - every rule also on the races with NO scratching after the open, where the price paid is the price shown and the
    runners that ran are the field at the bet: there the sheet and Test 98 are judged with nothing known after the open
  - round 81's rule as it ran, beside the corrected one, on the races WITH a scratching after the open, to show what
    the mismatch cost
  - the ladder's chances are saved in the walk cache (ladder_r82.npz), so a later round reads them back in minutes

    ROUND80_REUSE=yes python research/greyhound/topaz_round82.py DIR LABEL    (round 80's walk in the walk cache)

Counts, sums and rates only: no race, dog or price is printed. The model's inputs are named.
"""
import hashlib
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
import topaz_round73 as R73       # noqa: E402
import topaz_round79 as R79       # noqa: E402
import topaz_round80 as R80       # noqa: E402
import topaz_round81 as R81       # noqa: E402

TAG = "r82"
FAIR_UNDER = R81.FAIR_UNDER
GRID = R81.GRID
MARGINS = R81.MARGINS
NAMES = R81.NAMES
LADDER = "ladder_r82.npz"


def paid_at(grid: np.ndarray, ded: np.ndarray) -> np.ndarray:
    """The price paid at each ladder price (runners x prices): 1 + (price - 1) x (1 - TAB's deduction)."""
    g = np.asarray(grid, float)[None, :]
    dd = np.nan_to_num(np.asarray(ded, float), nan=0.0)[:, None]
    return 1 + (g - 1) * (1 - dd)


def ladder_rule(pg: np.ndarray, paid_g: np.ndarray, d: float) -> np.ndarray:
    """The best model's rule at each ladder price, as Test 98 reads it: its chance at least d over 1 / the price paid
    there, its fair price under $15."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.isfinite(pg) & (pg > 0) & (pg - 1 / paid_g >= d - 1e-12) & (1 / pg < FAIR_UNDER)


def band_orders(pg: np.ndarray, paid_g: np.ndarray, d: float, scale: float) -> tuple:
    """As round 81's, with the rule and the quarter-Kelly stake at each band end read at the price paid there."""
    ok = ladder_rule(pg, paid_g, d)
    valid = ok[:, :-1] & ok[:, 1:]
    k = R73.raw_kelly(pg, paid_g) / scale
    ks = np.minimum(k[:, :-1], k[:, 1:])
    return valid, np.where(valid, ks, 0.0)


def race_key(race: np.ndarray) -> str:
    """A fingerprint of the runner order, so a saved ladder is only read back onto the same rows."""
    return hashlib.sha256("|".join(map(str, race)).encode()).hexdigest()[:16]


def save_ladder(path: Path, key: str, res: dict) -> None:
    out = {"key": np.array(key)}
    for nm, (pg, pa) in res.items():
        idx = np.flatnonzero(np.isfinite(pa))
        out[f"i_{nm}"] = idx.astype(np.int32)
        out[f"g_{nm}"] = pg[idx].astype(np.float32)
        out[f"a_{nm}"] = pa[idx].astype(np.float32)
    np.savez_compressed(path, **out)


def load_ladder(path: Path, key: str, n: int, k: int) -> dict:
    """The saved ladder (each field's chances on the ladder and at TAB's actual price), or None if absent or for
    other rows."""
    if not path.exists():
        return None
    z = np.load(path)
    if str(z["key"]) != key:
        return None
    res = {}
    for nm, _ in NAMES:
        pg, pa = np.full((n, k), np.nan), np.full(n, np.nan)
        i = z[f"i_{nm}"]
        pg[i], pa[i] = z[f"g_{nm}"], z[f"a_{nm}"]
        res[nm] = (pg, pa)
    return res


def main(d, label):
    os.environ.pop("WALK_LEAD_MODEL", None)
    t0 = time.monotonic()
    bdir = os.environ.get("BETWATCH_DIR", "")
    print(f"# {label}: round 82, the band sheet on Test 98's footing for dogs scratched after the open\n")
    if not bdir or not os.path.isdir(bdir):
        print("No Betwatch files (BETWATCH_DIR): nothing to test")
        return 1
    x, R, XR, q, use, off_tab, tab, inputs = R67.build(d, t0)
    keep, drop = R79.live_inputs(inputs)
    XK = XR[keep]
    has70 = R67.read_saved(x, "r70", "c_f")
    print(f"Inputs known on the morning: {len(keep)} (dropped as BSP-based: {len(drop)}). Test 88's fit "
          f"{'is' if has70 else 'is NOT'} in the walk cache. {(time.monotonic() - t0) / 60:.0f} minutes in.\n")

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

    K = len(GRID)
    cdir = os.environ.get("WALK_CACHE_DIR", "")
    key = race_key(race)
    res = load_ladder(Path(cdir) / LADDER, key, len(R), K) if cdir else None
    if res is not None:
        print(f"## 2. The ladder, read back from the walk cache ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
    else:
        since_r = dates >= np.datetime64(R63.SINCE)
        book = R80.usual_book(R)
        nb = R.n_bet.values.astype(float)
        nl = np.clip(nb - pd.Series(np.ones(len(R))).groupby(race).transform("sum").values, 0, None)
        later_pred = book * nl / nb
        ran_book = book * (1 - nl / nb)
        inv_ours = ran_book * np.exp(XK.lp_ours.values.astype(float))
        pred, _ = R80.walk_tab_open(R, XK)
        inv_model = ran_book * R80.race_share(pred, race)
        print(f"## 2. The ladder, priced again ({(time.monotonic() - t0) / 60:.0f} minutes in)\n")
        lp_ours = XK.lp_ours.values.astype(float)
        month = pd.Series(R.date.values).dt.to_period("M").array
        price_r = R.price.values.astype(float)
        res = {nm: (np.full((len(R), K), np.nan), np.full(len(R), np.nan)) for nm, _ in NAMES}
        for i, (M, bst) in enumerate(models):
            nxt = models[i + 1][0] if i + 1 < len(models) else None
            blk = np.flatnonzero(since_r & (month >= M) & ((month < nxt) if nxt is not None else True)
                                 & np.isfinite(p))
            if not len(blk) or bst is None:
                continue
            pf = (lambda X, b=bst: b.predict(X, raw_score=True))
            for nm, inv_o, hold in R80.VARIANTS(inv_ours, inv_model):
                gap_races = pd.unique(race[blk][~np.isfinite(inv_o[blk]) | ~np.isfinite(later_pred[blk])])
                rows = blk[~np.isin(race[blk], gap_races)]
                if not len(rows):
                    continue
                sh = R80.Sheet(XK.iloc[rows], lp_ours[rows], inv_o[rows], later_pred[rows], race[rows], pf,
                               hold_book=hold)
                n = len(rows)
                res[nm][0][rows] = np.column_stack([sh.chance(np.full(n, g)) for g in GRID])
                res[nm][1][rows] = sh.chance(price_r[rows])
            print(f"{M}: {len(blk):,} runners priced on the ladder, {(time.monotonic() - t0) / 60:.0f} minutes in")
        if cdir:
            Path(cdir).mkdir(parents=True, exist_ok=True)
            save_ladder(Path(cdir) / LADDER, key, res)
            print("\nThe ladder is saved in the walk cache.")

    t["q_bsp"], _ = R58.corrected_bsp(t)
    tq = t.assign(p_bsp=t.q_bsp)
    paid = R68.paid_price(t)
    price = t.price.values.astype(float)
    ded = t.ded.fillna(0).values.astype(float)
    pgrid = paid_at(GRID, ded)
    since = R63.R36.in_period(t, R63.SINCE, None)
    clean = t.n_later.fillna(0).values == 0
    pm = on_t(p)
    m98 = R68.margin_bets(t, pm, R80.MARGIN)
    base = R67.model_chance(t, "c_f") if has70 else pm
    scale = R73.raw_kelly(base, paid)[R68.margin_bets(t, base, R80.MARGIN) & since].mean()
    u98 = R73.raw_kelly(pm, paid) / scale
    m98 &= u98 > 0
    flat = np.ones(len(t))
    jt = R81.band_of(price, GRID)
    T98 = "the best model on TAB's whole opening book (Test 98)"
    rules = {T98: dict(fm=m98 & since, km=m98 & since, uk=u98)}
    asran, extra = {}, {}
    for nm, lab in NAMES:
        pg, pa = on_t(res[nm][0]), on_t(res[nm][1])
        for dm in MARGINS:
            ok_a = R81.rule_at(pa, paid, dm) & since
            uk_a = R73.raw_kelly(pa, paid) / scale
            rules[f"{lab}, {dm * 100:.0f} points, at TAB's actual price"] = dict(fm=ok_a, km=ok_a & (uk_a > 0), uk=uk_a)
            valid, ks = band_orders(pg, pgrid, dm, scale)
            hit, uk_b = R81.fire(valid, ks, jt)
            hit &= since
            k = f"{lab}, {dm * 100:.0f} points, bands"
            rules[k] = dict(fm=hit, km=hit & (uk_b > 0), uk=uk_b)
            has = valid.any(axis=1) & since
            extra[k] = dict(set=has, flat_orders=R81.orders_flat(valid)[has], kelly_orders=valid.sum(axis=1)[has],
                            hit=hit)
            v0, k0 = R81.band_orders(pg, GRID, dm, scale)
            h0, u0 = R81.fire(v0, k0, jt)
            h0 &= since
            asran[k] = dict(fm=h0, km=h0 & (u0 > 0), uk=u0)

    def table(title, cut, rr):
        print(f"\n## {title}\n")
        print("| rule | flat: bets | flat: corrected BSP per unit (SE) | flat: corrected BSP units | flat: realised | "
              "quarter Kelly: bets | units staked | corrected BSP per unit (SE) | corrected BSP units | realised | "
              "luck (SD) | deepest fall | losing months |\n|" + "---|" * 13)
        for nm, r in rr.items():
            s = R68.staked(tq, r["fm"] & cut, paid, flat)
            fcell = (f"{s['n']:,} | {s['per']:+.1%} ({s['se']:.1%}) | {s['units']:+,.1f} | {s['real']:+,.1f}"
                     if s["n"] else "0 | | |")
            print(f"| {nm} | {fcell} | " + R73.kelly_row(t, tq, r["km"] & cut, paid, r["uk"]) + " |")

    allr = np.ones(len(t), bool)
    print(f"Races with a scratching after the open, February 2025 on: {int((since & ~clean).sum()):,} of "
          f"{int(since.sum()):,} runners; the quarter Kelly on Test 98's scale, {scale:.4f}. "
          f"{(time.monotonic() - t0) / 60:.0f} minutes in.")
    table("3. Every rule on Test 98's footing, February 2025 on", allr, rules)
    table("4. The races with no scratching after the open (nothing known after the open, in any rule)", clean, rules)
    mis = {T98: rules[T98]}
    for k in extra:
        mis[f"{k}, on Test 98's footing"] = rules[k]
        mis[f"{k}, as round 81 ran it"] = asran[k]
    table("5. The races with a scratching after the open: the corrected rule beside round 81's", ~clean, mis)

    print("\n## 6. By half: corrected BSP units / realised units, flat and at a quarter of Kelly\n")
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

    print("\n## 7. The band sheet's orders, February 2025 on\n")
    print("| rule | dogs given an order | BetMatic orders a dog, flat (median, most) | orders a dog, quarter Kelly (one a "
          "band: median, most) | fired | bets Test 98 makes too | Test 98's bets the sheet misses |\n|" + "---|" * 7)
    for nm, e in extra.items():
        fo, ko = e["flat_orders"], e["kelly_orders"]
        print(f"| {nm} | {int(e['set'].sum()):,} | {np.median(fo) if len(fo) else 0:.0f}, {fo.max() if len(fo) else 0} "
              f"| {np.median(ko) if len(ko) else 0:.0f}, {ko.max() if len(ko) else 0} | {int(e['hit'].sum()):,} | "
              f"{int((e['hit'] & m98 & since).sum()):,} | {int((m98 & since & ~e['hit']).sum()):,} |")

    print("\n## 8. At a quarter of Kelly, by who makes the bet (corrected BSP units / realised units, bets)\n")
    print("| rule | both | the sheet only | Test 98 only |\n|---|---|---|---|")
    for nm in extra:
        r = rules[nm]
        cells = []
        for mk, u in ((r["km"] & m98, r["uk"]), (r["km"] & ~m98, r["uk"]), (m98 & since & ~r["km"], u98)):
            s = R68.staked(tq, mk, paid, u)
            cells.append(f"{s['units']:+,.1f} / {s['real']:+,.1f} ({s['n']:,})" if s["n"] else "none")
        print(f"| {nm} | " + " | ".join(cells) + " |")

    shown = [T98] + [k for k in extra if " 2 points" in k or " 4 points" in k]
    print("\n## 9. By three months, a quarter of Kelly: corrected BSP units / realised units\n")
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
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "topaz round 82")
