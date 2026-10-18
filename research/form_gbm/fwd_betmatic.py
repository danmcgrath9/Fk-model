"""Forward test of the BetMatic method only (14 Oct 2026, founder: "Forward test I only want the model that we would be
using with betmatic").

For every meeting since 5 Oct: the order file BetMatic would have been sent before the market (betmatic_orders.py rules:
model price $1.60-$15, minimum odds 0.95 x (1.2 / p_model^0.82)^(1/0.78), 8 price steps each sized at the next step,
no first starters, no first-up/bounce blocks, EARLY runners $8 or shorter only, nothing at 3x our price), built from
the meeting's FIRST priced file (git history: the price the model made before the race, never re-made after), filled
at the opening price in the meeting's first saved market snapshot, the race-level first-starter rule applied (no bets
in a race where a first starter opens $6 or shorter), scratched runners void, winnings less the race's scratching
deduction (deductions.py). $100 a unit. CLV = opening price over Betfair SP.

    python fwd_betmatic.py RESULTS_TXT [RESULTS_TXT ...] OUT_MD     (meeting_results.py output)"""
import json, os, re, subprocess, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from betmatic_orders import tiers, SHADE
from opens import parse_opens
from deductions import race_deductions
L = os.path.join(here, "../../data/live_bets"); REPO = os.path.join(here, "../..")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
# (label, results meeting id, day prefix, gtag, opening snapshot = the first saved file with the market up)
MEETINGS = [
    ("Mon 5 Oct Pakenham", "pakenham-synthetic-20261005", "2026-10-05-pakenham", "", "2026-10-05-pakenham-prices.txt"),
    ("Tue 6 Oct Mildura", "mildura-20261006", "2026-10-06-mildura", "g4", "2026-10-06-mildura-prices-monday.txt"),
    ("Wed 7 Oct Geelong", "geelong-20261007", "2026-10-07-geelong", "s6", "2026-10-07-geelong-prices-monday.txt"),
    ("Thu 8 Oct Kyneton", "kyneton-20261008", "2026-10-08-kyneton", "g4", "2026-10-08-kyneton-prices-wed.txt"),
    ("Fri 9 Oct Ballarat", "ballarat-20261009", "2026-10-09-ballarat", "g4", "2026-10-09-ballarat-prices.txt"),
    ("Fri 9 Oct Cranbourne", "cranbourne-20261009", "2026-10-09-cranbourne", "g4", "2026-10-09-cranbourne-prices-thu930.txt"),
    ("Sat 10 Oct Caulfield", "caulfield-20261010", "2026-10-10-caulfield", "g4", "2026-10-10-caulfield-prices-wed927pm.txt"),
    ("Sun 11 Oct Seymour", "seymour-20261011", "2026-10-11-seymour", "g4", "2026-10-11-seymour-prices-fri115.txt"),
    ("Tue 13 Oct Kilmore", "kilmore-20261013", "2026-10-13-kilmore", "s5", "2026-10-13-kilmore-prices-mon745pm.txt"),
    ("Wed 14 Oct Caulfield", "caulfield-20261014", "2026-10-14-caulfield", "g4", "2026-10-14-caulfield-prices-mon748pm.txt"),
    ("Thu 15 Oct Warrnambool", "warrnambool-20261015", "2026-10-15-warrnambool", "g4", "2026-10-15-warrnambool-prices.txt"),
    ("Fri 16 Oct Cranbourne", "cranbourne-20261016", "2026-10-16-cranbourne", "g4", "2026-10-16-cranbourne-prices.txt"),
    ("Sat 17 Oct Caulfield", "caulfield-20261017", "2026-10-17-caulfield", "g4", "2026-10-17-caulfield-prices.txt"),
    ("Sat 17 Oct Bendigo", "bendigo-20261017", "2026-10-17-bendigo", "g4", "2026-10-17-bendigo-prices.txt"),
    ("Sat 17 Oct Wodonga", "wodonga-20261017", "2026-10-17-wodonga", "g4", "2026-10-17-wodonga-prices.txt"),
    ("Sat 17 Oct Avoca", "avoca-20261017", "2026-10-17-avoca", "g4", "2026-10-17-avoca-prices.txt"),
    ("Sun 18 Oct Horsham", "horsham-20261018", "2026-10-18-horsham", "g4", "2026-10-18-horsham-prices.txt"),
    ("Sun 18 Oct Moe", "moe-20261018", "2026-10-18-moe", "g4", "2026-10-18-moe-prices.txt"),
]   # add each meeting the founder bets; the opening snapshot is the first saved file with the market up
def git_first(path):
    """The file as first committed (the price made before the race), or None."""
    h = subprocess.run(["git", "-C", REPO, "log", "--diff-filter=A", "--format=%h", "--", path], capture_output=True, text=True).stdout.split()
    if not h: return None, None
    r = subprocess.run(["git", "-C", REPO, "show", f"{h[-1]}:{path}"], capture_output=True, text=True)
    return (json.loads(r.stdout), h[-1]) if r.returncode == 0 else (None, h[-1])
def at(commit, path, default):
    r = subprocess.run(["git", "-C", REPO, "show", f"{commit}:{path}"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else default

*res_ps, out_p = sys.argv[1:]
res, cur = {}, None
for res_p in res_ps:
    for l in open(res_p):
        m = re.match(r"## (\S+):", l)
        if m: cur = m.group(1); continue
        m = re.match(r"R(\d+) (.+?)\s+finish (\S+)\s+SP (\S+)\s+BSP (\S+)", l)
        if m and cur:
            res[(cur, int(m.group(1)), norm(m.group(2)))] = (None if m.group(3) == "None" else int(m.group(3)), None if m.group(5) == "None" else float(m.group(5)))
head = ["# Forward test: the BetMatic method only, settled", "",
        "Every meeting since 5 Oct run as BetMatic would have run it: the pre-open order file from the model's first price for the",
        "meeting (made before the race, never re-made), filled at the opening price, the order file's price steps (3 from 14 Oct), first-starter race rule,",
        "scratched runners void, winnings less scratching deductions. In units (paper). CLV = opening price / Betfair SP.", "",
        "| Meeting | Orders | Horses filled | Won | Staked | P/L | Avg CLV | Beat BSP |", "|---|---|---|---|---|---|---|---|"]
detail = ["", "## Every fill", "", "| Meeting | Race | Horse | Ours | Min odds | Opened | Steps filled | Stake | Finish | BSP | Deduction | P/L |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
T = collections.Counter(); clv_all = []
for label, mid, pre, g, snap in MEETINGS:
    B = f"{pre}-{g}" if g else pre
    v, c = git_first(f"data/live_bets/{B}-v6.json")
    if v is None or not any(k[0] == mid for k in res):
        head.append(f"| {label} | not run yet | | | | | | |"); continue
    fs = set(at(c, f"data/live_bets/{B}-first-starters.json", None) or json.load(open(f"{L}/{B}-first-starters.json")))
    fu = at(c, f"data/live_bets/{B}-first-up-blocks.json", None) or json.load(open(f"{L}/{B}-first-up-blocks.json"))
    opens = {}
    for l in open(f"{L}/{snap}"):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit() and not pa[2].upper().startswith("SCR"):
            fk, tab = parse_opens(", ".join(pa[3:])); opens[(int(pa[0]), norm(pa[1]))] = fk or tab
    field = collections.Counter(int(r["race"]) for r in v)
    # race-level first-starter rule: no bets where a first starter opens $6 or shorter
    fs_short = {int(k.split("|")[0]) for k in fs if (opens.get((int(k.split("|")[0]), norm(k.split("|", 1)[1]))) or 99) <= 6}
    ded, _ = race_deductions(pre)
    sent = None   # from 14 Oct a real pre-open order file exists (built before the open, never rebuilt): use it exactly
    if os.path.exists(f"{L}/{pre}-betmatic-preopen.csv"):
        import csv
        sent = collections.defaultdict(list)
        for o in csv.DictReader(open(f"{L}/{pre}-betmatic-preopen.csv")):
            sent[(int(o["race"]), norm(o["horse"]))].append((float(o["min_odds"]), float(o["stake_units"]), None,
                                                             float(o["max_odds"]) if o.get("max_odds") else 3 * float(o["our_price"])))
    n_orders = n = w = 0; st_t = pl = 0.0; clv = []
    cands = []   # (race, horse, ours, steps [(min, stake, _, cap)], cap)
    if sent is not None:   # the order file actually built before the open: used exactly, never rebuilt
        names = {(int(r["race"]), norm(r["horse"])): r["horse"] for r in v}
        import csv
        ours_of = {(int(o["race"]), norm(o["horse"])): (o["horse"], float(o["our_price"])) for o in csv.DictReader(open(f"{L}/{pre}-betmatic-preopen.csv"))}
        for key, ts in sent.items():
            cands.append((key[0], ours_of[key][0], ours_of[key][1], ts, ts[0][3]))
    else:
        for r in v:
            k = f"{int(r['race'])}|{r['horse']}"; pm = r.get("p_model", r["p"]); ours = 1 / pm; blk = fu.get(k, "")
            if k in fs or (blk and not blk.startswith("EARLY")) or not 1.6 <= ours <= 15: continue
            mo = round(SHADE * (1.2 / pm ** 0.82) ** (1 / 0.78), 2); cap = min(3 * ours, 8.0 if blk.startswith("EARLY") else 1e9)
            if mo >= cap: continue
            ts = tiers(mo, cap, lambda t, pm=pm: pm ** 0.82 * t ** -0.22, r.get("only_ride", False), field[int(r["race"])])
            cands.append((int(r["race"]), r["horse"], ours, ts, cap))
    if os.environ.get("RESTAKE"):   # every ladder re-sized with today's stake_rule.py; the prices and steps are kept as built
        import stake_rule
        re_c = []
        for rc, horse, ours, ts, cap in cands:
            if len(ts[0]) < 4:   # built here by tiers(), which already sizes with today's stake_rule.py
                re_c.append((rc, horse, ours, ts, cap)); continue
            pm = 1 / ours; out = []
            for cp in sorted({x[3] for x in ts}):            # one ladder per ceiling (the under-$4 ladder has its own)
                lad = sorted(x for x in ts if x[3] == cp); prev = 0.0
                for k, x in enumerate(lad):
                    tp = lad[k + 1][0] if k + 1 < len(lad) else x[0]
                    tgt = stake_rule.stake(pm ** 0.82 * tp ** -0.22, tp); add = max(0.0, tgt - prev); prev = max(prev, tgt)
                    out.append((x[0], round(add, 2), None, cp))
            re_c.append((rc, horse, ours, out, cap))
        cands = re_c
    for rc, horse, ours, ts, cap in sorted(cands, key=lambda c: (c[0], c[1])):
        r = {"race": rc, "horse": horse}; mo = ts[0][0]
        n_orders += len(ts)
        op = opens.get((rc, norm(horse)))
        if op is None or rc in fs_short: continue
        filled = [x for x in ts if op >= x[0]]
        if not filled: continue
        over_cap = op >= cap   # the open is past the 3x (or EARLY $8) ceiling: a min-odds order still fills
        st = round(sum(x[1] for x in filled), 2)
        f, bsp = res.get((mid, rc, norm(r["horse"])), (None, None))
        if f is None:
            detail.append(f"| {label} | R{rc} | {r['horse']} | ${ours:.2f} | ${mo:.2f} | ${op:g} | {len(filled)} of {len(ts)} | {st:.2f}u | scratched | | | 0 |"); continue
        d = ded.get(rc, 0.0); won = f == 1; p = st * (op - 1) * (1 - d) if won else -st
        n += 1; w += won; st_t += st; pl += p
        if over_cap: T["cap_n"] += 1; T["cap_st"] += st; T["cap_pl"] += p
        if bsp: clv.append(op / bsp)
        detail.append(f"| {label} | R{rc} | {r['horse']} | ${ours:.2f} | ${mo:.2f} | ${op:g} | {len(filled)} of {len(ts)} | {st:.2f}u | {f} | "
                      f"{'$%.2f' % bsp if bsp else ''} | {'%.0fc' % (100 * d) if d else ''} | {p:+.2f} |" + (" opened past the 3x ceiling" if over_cap else ""))
    clv_all += clv; T.update(o=n_orders, n=n, w=w); T["st"] += st_t; T["pl"] += pl
    head.append(f"| {label} | {n_orders} | {n} | {w} | {st_t:.2f}u | {pl:+.2f}u | {sum(clv)/len(clv) if clv else 0:.2f} | {sum(x > 1 for x in clv)}/{len(clv)} |")
roi = 100 * T["pl"] / T["st"] if T["st"] else 0
head.append(f"| **Total** | **{T['o']}** | **{T['n']}** | **{T['w']}** | **{T['st']:.2f}u** | **{T['pl']:+.2f}u ({roi:+.0f}%)** | "
            f"**{sum(clv_all)/len(clv_all) if clv_all else 0:.2f}** | **{sum(x > 1 for x in clv_all)}/{len(clv_all)}** |")
head += ["", f"Of these, {T['cap_n']} opened at or past the ceiling (3x our price, $8 for EARLY runners), where the rules would not bet: "
         f"{T['cap_st']:.2f}u staked, {T['cap_pl']:+.2f}u. With a maximum price on the order: {T['n'] - T['cap_n']} bets, {T['st'] - T['cap_st']:.2f}u, "
         f"{T['pl'] - T['cap_pl']:+.2f}u ({100 * (T['pl'] - T['cap_pl']) / max(T['st'] - T['cap_st'], 1e-9):+.0f}%)."]
open(out_p, "w").write("\n".join(head + detail) + "\n"); print("\n".join(head + detail))
