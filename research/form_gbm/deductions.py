"""Scratching deductions for bets struck at the open (13 Oct 2026, founder: "scratchings, can we do that?").
A fixed-odds win bet takes a deduction from its WINNINGS for every runner scratched after it was struck, set by the
scratched runner's price when it was scratched (TAB/Sportsbet schedules: about 0.95 / price, e.g. $3.00 -> 31c, capped
per runner; summed per race). An open bet is struck before the scratchings, so every runner that was in the market
and later scratched counts.

Source: the meeting's own saved prices files (data/live_bets/<prefix>-prices*.txt). A runner priced (not SCR) in an
earlier file and SCR in the final one was scratched after the market opened; its last price before scratching is its
last priced line, or the "last X" / "fk_open X" kept on its SCR line (scratchings.py writes these from 13 Oct 2026).
The final file is <prefix>-prices.txt; earlier ones are ordered by how many runners they already had scratched.
    python deductions.py 2026-10-10-caulfield        -> {race: deduction} and the runners behind it"""
import glob, os, re, sys
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/live_bets")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
PER_RUNNER_CAP, PER_RACE_CAP = 0.90, 0.95

def _read(fn):
    d = {}
    for l in open(fn):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) < 3 or not pa[0].isdigit(): continue
        k = (int(pa[0]), norm(pa[1])); rest = " ".join(pa[2:])
        if pa[2].upper().startswith("SCR"):
            m = re.search(r"last\s+([\d.]+)", rest) or re.search(r"fk_open\s+([\d.]+)", rest)
            d[k] = ("SCR", float(m.group(1)) if m else None, pa[1])
        else:
            try: d[k] = ("RUN", float(pa[2]), pa[1])
            except ValueError: pass
    return d

def actual_deductions(prefix):
    """The deductions TAB actually applied, from the founder's account (14 Oct 2026, founder: "This is deductions from TAB
    at opening"): data/live_bets/<prefix>-deductions-actual.txt, lines "race, cents  # horse". They replace the estimate
    for those races, because the estimate (0.95 / price of every runner scratched after the open, the TAB schedule) ran
    2.5x too high on the first meeting checked (Caulfield 14 Oct: 59c estimated against 24c applied)."""
    fn = f"{L}/{prefix}-deductions-actual.txt"
    if not os.path.exists(fn): return {}
    out = {}
    for l in open(fn):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 2 and pa[0].isdigit(): out[int(pa[0])] = float(pa[1]) / 100
    return out

def race_deductions(prefix):
    """-> ({race: deduction 0..0.95}, {race: [(horse, price)]}). Races with no late scratching are absent (0).
    Actual TAB deductions (actual_deductions) replace the estimate wherever they are recorded."""
    d, w = _estimated(prefix); d.update(actual_deductions(prefix)); return d, w

def _estimated(prefix):
    final_fn = f"{L}/{prefix}-prices.txt"
    if not os.path.exists(final_fn): return {}, {}
    final = _read(final_fn)
    early = [f for f in glob.glob(f"{L}/{prefix}-prices*.txt") if f != final_fn and not f.endswith("-fields.txt")]
    snaps = sorted((_read(f) for f in early), key=lambda d: sum(v[0] == "SCR" for v in d.values()))
    ded, who = {}, {}
    for k, (st, px, name) in final.items():
        if st != "SCR": continue
        last = None
        for s in snaps:   # the latest earlier snapshot where it was still running gives its last price
            if s.get(k, ("",))[0] == "RUN" and s[k][1] and s[k][1] > 1: last = s[k][1]
        if last is None and px: last = px
        if not last or last <= 1: continue
        who.setdefault(k[0], []).append((name, last))
    for rc, lst in who.items():
        ded[rc] = min(PER_RACE_CAP, sum(min(PER_RUNNER_CAP, 0.95 / p) for _, p in lst))
    return ded, who

if __name__ == "__main__":
    d, w = race_deductions(sys.argv[1])
    for rc in sorted(w): print(f"R{rc}: {100*d[rc]:.0f}c  " + ", ".join(f"{n} ${p:g}" for n, p in w[rc]))
    if not w: print("no runner scratched after an earlier saved price")
