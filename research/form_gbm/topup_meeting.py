"""The 30-90 min after-open check for one meeting (27 Oct 2026), from scripts/fluc_meeting.py output + the meeting's v6
json. Judged on the AVERAGE price at each check point (30/40/45/50/60/90 min after the race's open); the best book is
shown beside it, never used to qualify.
  (A) horses we hold: still clear the live minimum (edge 1.15 under $4, else 1.2), not 20%+ out from the open:
      top up the shortfall (target at this price minus what filled at the open). Paper.
  (B) new horses: edge 1.3, not 20%+ out, ours $1.60-$15, under 3x ours, not in a first-starter race. Real bets.
Twitter units = half the FULL rule stake at that price, max 5u (the Twitter book takes no open bets), so a held horse
already filled in full is still a Twitter tip with a 0u book top-up. Prints the tweet draft in the founder's format (27 Oct:
"the book (if it's multiple say multiple), the race - number - horse name - units").
    python3.13 topup_meeting.py FLUC_CSV V6_JSON FIRST_STARTERS_JSON ["Horse=filled_units;Horse=..."] [--upto m60] [--track=Bendigo]"""
import sys, csv, json, collections, stake_rule
args = [a for a in sys.argv[1:] if not a.startswith("--")]
upto = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--upto=")), "m90")
L = open(args[0]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip().splitlines()
R = list(csv.DictReader(L)); V = {(x["race_id"], x["horse_id"]): x for x in json.load(open(args[1]))}
FSR = {int(s.split("|")[0]) for s in json.load(open(args[2]))}
held = {}
for h in (args[3].split(";") if len(args) > 3 else []):
    if h.strip(): n, _, u = h.partition("="); held[n.strip().lower()] = float(u or 0)
W = [c for c in ("m30", "m40", "m45", "m50", "m60", "m90") if c <= upto or upto == "m90"]
BOOK = {"tab": "TAB", "tabtouch": "TABtouch", "sportsbet": "Sportsbet", "ladbrokes": "Ladbrokes", "neds": "Neds",
        "pointsbet": "PointsBet", "betr": "Betr", "unibet": "Unibet", "bet365": "Bet365", "betright": "BetRight",
        "elitebet": "Elitebet", "palmerbet": "Palmerbet", "picnicbet": "Picnicbet", "betdeluxe": "BetDeluxe"}
TIERS = (1.0, 1.25, 1.5)
def target(p, t0, E):
    q = 1 / p
    if not (1.6 <= q <= 15) or t0 >= 3 * q: return 0.0, None
    mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
    if t0 < mo: return 0.0, mo
    ts = [mo * k for k in TIERS if mo * k < 3 * q]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if t0 >= t: tot += add
    return tot, mo
byr = collections.defaultdict(list)
for r in R:
    if r["scratched"] == "0" and (r["race_id"], r["horse_id"]) in V: byr[int(r["race"])].append(r)
A, B = [], []
for rn in sorted(byr):
    xs = byr[rn]; s = sum(float(V[(x["race_id"], x["horse_id"])]["p_model"]) for x in xs)
    for x in xs:
        if not x["open"]: continue
        p = float(V[(x["race_id"], x["horse_id"])]["p_model"]) / s; op = float(x["open"]); nm = x["name"].strip()
        mine = nm.lower() in held
        if not mine and rn in FSR: continue
        for c in W:
            if not x[c] or float(x[c]) / op >= 1.2: continue
            t = float(x[c]); st, mo = target(p, t, (1.15 if t < 4 else 1.2) if mine else 1.3)
            full = st
            if mine: st = max(0.0, st - held[nm.lower()])
            if full > 0:
                bb = [b for b in x["best_bookies"].split() if b]
                book = "Multiple" if len(bb) > 1 else (BOOK.get(bb[0], bb[0].title()) if bb else "?")
                (A if mine else B).append(dict(race=rn, num=x["number"], horse=nm, ours=1 / p, open=op, when=c[1:], avg=t,
                                               best=x["best_now"], books=" ".join(BOOK.get(b, b) for b in bb), book=book,
                                               mo=mo, units=round(st, 2), tw=round(min(5.0, full / 2), 2)))
                break
for lab, L_ in (("(A) TOP-UP, horses we hold (paper)", A), ("(B) NEW HORSES (real bets, your OK)", B)):
    print(f"\n## {lab}\n")
    if not L_: print("none"); continue
    print("| race | no. | horse | ours | open | fired | avg | best now (books) | take if still | units | Twitter |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for b in L_:
        print(f"| R{b['race']} | {b['num']} | {b['horse']} | ${b['ours']:.2f} | ${b['open']:g} | {b['when']} min | ${b['avg']:g} | "
              f"${b['best']} ({b['books'][:60]}) | ${b['mo']:.2f} | {b['units']:.2f}u | {b['tw']:.2f}u |")
tips = sorted(A + B, key=lambda b: (b["race"], b["num"]))
# Tweet drafts, one per race (founder 27 Oct: "Need the odds. Do it something like this", Anthony Don's layout:
# TRACK R1 - DAY / horse - $best BOOK / $avg OTHERS / units WIN). Founder picked option 2 (27 Oct): one horse emoji on
# the title, the price on its own line, and our rated price under the units. Best book named, "MULTIPLE" when several share it.
import datetime as _dt
track = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--track=")), "")
def _day(rid):
    d = rid.rsplit("_", 2)[1]; return _dt.date(2000 + int(d[4:6]), int(d[2:4]), int(d[0:2])).strftime("%A").upper()
rid_of = {int(r["race"]): r["race_id"] for r in R}
print("\n## Tweet drafts (one per race)\n")
if not tips: print("(no tips)")
for rn in sorted({b["race"] for b in tips}):
    lines = [f"{track.upper()} R{rn} - {_day(rid_of[rn])} \U0001F3C7", ""]
    for b in [t for t in tips if t["race"] == rn]:
        best = float(b["best"]) if b["best"] else b["avg"]
        book = "MULTIPLE" if b["book"] == "Multiple" else b["book"].upper()
        px = f"${best:.2f} {book} / ${b['avg']:.2f} OTHERS" if best > b["avg"] + 0.005 else f"${b['avg']:.2f} ALL BOOKS"
        lines += [f"{b['num']}. {b['horse'].upper()}", px, f"{b['tw']:g} units WIN", "", f"Rated ${b['ours']:.2f}.", ""]
    print("\n".join(lines).rstrip() + "\n\n---\n")
