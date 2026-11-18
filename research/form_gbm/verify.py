"""verify.py: check the work before it reaches the founder or BetMatic (17 Nov 2026, founder: "As long as you think its
fine", after a week of misses that were all unverified claims: a Mercer card priced off a stale cross-bookmaker snapshot,
a paper fill reported as a real bet, deductions filed against the wrong meeting).

    python3.13 verify.py                 observe mode: log what would have been blocked, exit 0
    python3.13 verify.py --enforce       exit 1 when anything is at BLOCK level
    python3.13 verify.py --day 2026-11-17
    python3.13 verify.py --all           the settle cross-check over every settled meeting (default: the last 7 days)
    python3.13 verify.py --selftest      plant each known miss in a scratch folder and check it is caught

OBSERVE MODE FIRST (the gate is new: log, read the false positives, then enforce). Every run appends a block to
data/live_bets/verify-log.md (the last 60 blocks are kept).

What it checks, from today on unless noted:
  sheets      every order sheet of record: a saddlecloth number on every order, dollars = units x the meeting's unit,
              minimum above our price, minimum <= maximum, maximum within the 6x ceiling
  cards       every Mercer / no-Mercer card: each horse is on its meeting's sheet, units = the open-book fill, the
              no-Mercer price = Form King's open and its rated price = ours, a scratched horse is marked, an open-book
              bet missing from the card is named; a Mercer card carries the time its prices were pulled
              ("prices_as_at") and no price sits well above the last pull; a card marked "posted": true is locked
              (tips are locked once tweeted) and its prices are no longer checked
  9am list    price now at or above the take price, take price = 1.05 x the blend, blend $1.60-$15, stake = to win /
              (price - 1)
  deductions  every race in a <prefix>-deductions-actual.txt has a scratched runner in that meeting (the founder's
              Kyneton figures were filed against Wangaratta, where three of the four races had no scratching)
  betmatic    every sent sheet (a -ledger.csv): how many orders BetMatic's own status confirms as placed; a ledger
              never read back is named, so a paper fill is never reported as a bet
  settle      DIFFERENTIAL: the running record (running_record.py) against the day page's own settle
              (betmatic_html.py, run on a blank page) for every settled meeting, and against the no-Mercer card for
              the day; any difference in bets, units or P/L is named with the likely reason. Both paths pay a winner
              after TAB's deduction as the founder reported it; a winner that differs would block
"""
import argparse, collections, csv, datetime as dt, glob, html, json, os, re, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import running_record as rr
from opens import parse_opens

norm = rr.norm
UNIT_DEFAULT = 50.0                                  # founder, 14 Nov 2026: "$50 units"
UNIT_FOR = {"2026-11-14-dunkeld": 25.0}              # founder, 14 Nov: "$25 units for just dunkeld, no where else"
CEIL = 6.0                                           # the 6x ceiling (founder, 12 Nov)
MERCER_STALE_MIN = 45                                # a Mercer card's prices older than this are re-pulled before posting
FULL_UNITS_FROM = "2026-11-12"                       # cards carry the full model stake from Thu 12 Nov (half before)
SETTLE_DAYS = 7                                      # the settle cross-check re-runs meetings this recent (--all for every one)
money = lambda s: float(str(s).replace("$", "").replace(",", "").strip())


def read_prices(L, P):
    px = {}
    f = f"{L}/{P}-prices.txt"
    if not os.path.exists(f):
        return px
    for l in open(f):
        pa = [x.strip() for x in l.split("#")[0].split(",")]
        if len(pa) >= 3 and pa[0].isdigit():
            scr = pa[2].upper().startswith("SCR")
            fk, tab = (None, None) if scr else parse_opens(", ".join(pa[3:]))
            try:
                now = None if scr else float(pa[2])
            except ValueError:
                now = None
            px[(int(pa[0]), norm(pa[1]))] = dict(now=now if now and now > 1 else None, open=fk or tab, scr=scr)
    return px


def open_fills(L, P):
    """The open book for one meeting, as running_record.py and betmatic_html.py count it."""
    px = read_prices(L, P)
    by = collections.OrderedDict()
    for o in csv.DictReader(open(rr.sheet_for(P, L))):
        k = (int(o["race"]), norm(o["horse"]))
        p = px.get(k)
        if not p or p["scr"] or p["open"] is None:
            continue
        if p["open"] < float(o["min_odds"]) or (o.get("max_odds") and p["open"] > float(o["max_odds"])):
            continue
        b = by.setdefault(k, dict(race=k[0], horse=o["horse"], units=0.0, open=p["open"], rated=float(o["our_price"])))
        b["units"] += float(o["stake_units"])
    return by


def check_sheets(L, today, F):
    for f in sorted(glob.glob(f"{L}/2*-betmatic-preopen.csv")):
        P = os.path.basename(f)[:-len("-betmatic-preopen.csv")]
        if P[:10] < today:
            continue
        unit = UNIT_FOR.get(P, UNIT_DEFAULT)
        rows = list(csv.DictReader(open(f)))
        bad = collections.Counter()
        for o in rows:
            u, ours = float(o["stake_units"]), float(o["our_price"])
            lo, hi = float(o["min_odds"]), float(o["max_odds"] or 0)
            if not str(o.get("number", "")).strip().isdigit():
                bad[f"no saddlecloth number (R{o['race']} {o['horse']})"] += 1
            if o["stake_dollars"].strip() != f"{u * unit:.0f}":
                bad[f"dollars are not units x ${unit:g}"] += 1
            if lo <= ours:
                bad[f"minimum ${lo:g} is not above our price ${ours:g} (R{o['race']} {o['horse']})"] += 1
            if hi and lo > hi:
                bad[f"minimum above maximum (R{o['race']} {o['horse']})"] += 1
            if hi and hi > CEIL * ours + 0.05:
                bad[f"maximum ${hi:g} is over {CEIL:g}x our ${ours:g} (R{o['race']} {o['horse']})"] += 1
        for msg, n in bad.items():
            F.append(("BLOCK", f"sheet {P}", f"{msg}" + (f": {n} orders" if n > 1 else "")))
        if not rows:
            F.append(("CHECK", f"sheet {P}", "the sheet has no orders"))


def card_day(d, year):
    try:
        return dt.datetime.strptime(f"{d['date']} {year}", "%d %B %Y").date().isoformat()
    except (KeyError, ValueError):
        return None


def prefix_for(L, day, name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    for cand in (slug, slug.split("-")[0]):
        if os.path.exists(f"{L}/{day}-{cand}-betmatic-preopen.csv"):
            return f"{day}-{cand}"
    return None


def cards(C, year):
    out = []
    for f in sorted(glob.glob(f"{C}/card_*_plain_open.json") + glob.glob(f"{C}/card_*_mercer_now.json")):
        try:
            d = json.load(open(f))
        except ValueError:
            continue
        day = card_day(d, year)
        if day:
            out.append((day, "mercer" if f.endswith("_mercer_now.json") else "plain", os.path.basename(f), d))
    return out


def check_cards(L, C, today, now, F):
    for day, kind, fn, d in cards(C, today[:4]):
        if day < today:
            continue
        if kind == "mercer" and not d.get("posted"):       # once tweeted a card is locked: its prices are history
            t = d.get("prices_as_at")
            if not t:
                F.append(("CHECK", f"card {fn}", "no prices_as_at: the time its prices were pulled is not on the card"))
            else:
                try:
                    at = dt.datetime.fromisoformat(t)
                    if at.tzinfo is None:                 # a bare time is Melbourne time
                        at = at.replace(tzinfo=now.tzinfo)
                    age = (now - at).total_seconds() / 60
                    if age > MERCER_STALE_MIN:
                        F.append(("CHECK", f"card {fn}", f"prices are {age:.0f} minutes old: pull again before it is posted"))
                except (ValueError, TypeError):
                    F.append(("CHECK", f"card {fn}", f"prices_as_at {t!r} is not a time"))
        for m in d.get("meetings", []):
            P = prefix_for(L, day, m["name"])
            if not P:
                F.append(("BLOCK", f"card {fn}", f"{m['name']}: no order sheet for {day}")); continue
            fills, px = open_fills(L, P), read_prices(L, P)
            on_card = set()
            for b in m["bets"]:
                k = (int(b["race"]), norm(b["horse"])); on_card.add(k)
                who = f"{m['name']} R{b['race']} {b['horse']}"
                p, fl = px.get(k), fills.get(k)
                if p is None:
                    F.append(("BLOCK", f"card {fn}", f"{who}: not in the meeting's prices file")); continue
                if p["scr"] and not b.get("scr"):
                    F.append(("BLOCK", f"card {fn}", f"{who}: scratched, and the card does not mark it"))
                if b.get("scr"):
                    continue
                if fl is None:
                    F.append(("CHECK", f"card {fn}", f"{who}: " + (f"the prices file has no opening price yet, so the card's "
                              f"{b['price']} is unconfirmed" if p["open"] is None else
                              f"on the card, and Form King's open ${p['open']:g} fills nothing on the sheet")))
                    continue
                if abs(money(b["units"].rstrip("u")) - fl["units"]) > 0.011:
                    F.append(("CHECK", f"card {fn}", f"{who}: card {b['units']}, the sheet fills {fl['units']:.2f}u at the open"))
                price = money(b["price"])
                if kind == "plain":
                    if abs(price - fl["open"]) > 0.011:
                        F.append(("BLOCK", f"card {fn}", f"{who}: card ${price:g}, Form King's open ${fl['open']:g}"))
                    if b.get("rated") and abs(money(b["rated"]) - fl["rated"]) > 0.011:
                        F.append(("BLOCK", f"card {fn}", f"{who}: rated {b['rated']}, the sheet has ${fl['rated']:.2f}"))
                elif not d.get("posted") and p["now"] and price > p["now"] * 1.10:
                    F.append(("CHECK", f"card {fn}", f"{who}: card ${price:g} against ${p['now']:g} at the last pull"))
            for k, fl in fills.items():
                if k not in on_card:
                    F.append(("CHECK", f"card {fn}", f"{m['name']} R{fl['race']} {fl['horse']} {fl['units']:.2f}u is an open-book "
                              f"bet and is not on the card"))


def check_9am(L, today, F):
    for f in sorted(glob.glob(f"{L}/{today}-*-9am.csv")):
        P = os.path.basename(f)[:-len("-9am.csv")]
        for r in csv.DictReader(open(f)):
            who = f"R{r['race']} {r['horse']}"
            now, take, blend = float(r["price_now"]), float(r["take_at_or_above"]), float(r["blend_price"])
            win, stake = float(r["to_win"]), float(r["stake_a_bookie"])
            if now + 1e-9 < take:
                F.append(("BLOCK", f"9am {P}", f"{who}: price now ${now:g} is under the take price ${take:g}"))
            if abs(take - 1.05 * blend) > 0.02:
                F.append(("BLOCK", f"9am {P}", f"{who}: take price ${take:g} is not 1.05 x the blend ${blend:g}"))
            if not 1.6 <= blend <= 15:
                F.append(("BLOCK", f"9am {P}", f"{who}: blend price ${blend:g} is outside $1.60-$15"))
            if abs(stake - win / (now - 1)) > 1.0:
                F.append(("BLOCK", f"9am {P}", f"{who}: stake ${stake:g} is not ${win:g} / (price {now:g} - 1)"))
        # THE WHOLE BOOK (18 Nov research, night/r9/m_exact.py): when horses are scratched shortly before 9am and the
        # prices have not been re-framed yet, the race's book adds to well under its usual (1.23 on best prices, 1.33 on
        # the average, never under 1.11 in our own pulls) and every runner left reads as over the odds. Geelong 4 Jun
        # and Ballarat 12 Jul 2026 had books of 0.51-0.99; a bet taken then carries the deduction. Flag, never bet blind.
        px = read_prices(L, P); listed = {int(r["race"]) for r in csv.DictReader(open(f))}
        for rc in sorted(listed):
            nows = [p["now"] for k, p in px.items() if k[0] == rc and not p["scr"] and p["now"]]
            if len(nows) >= 4 and sum(1 / x for x in nows) < 1.08:
                F.append(("CHECK", f"9am {P}", f"R{rc}: the prices add to {sum(1 / x for x in nows):.2f} of a book (usual 1.23 or more): they may "
                          f"pre-date a scratching, and a bet at them would carry the deduction"))


def check_9am_bets(L, today, F):
    """The 9am bets (blend_9am_v2.py, bet by the founder from 19 Nov 2026 at the open book's units)."""
    for f in sorted(glob.glob(f"{L}/{today}-*-9am-v2.csv")):
        P = os.path.basename(f)[:-len("-9am-v2.csv")]
        for r in csv.DictReader(open(f)):
            if "stake_units" not in r: continue
            who = f"R{r['race']} {r['horse']}"
            best, take, fair = float(r["best_now"]), float(r["take_at_or_above"]), float(r["fair_price"])
            u, d = float(r["stake_units"]), float(r["stake_dollars"])
            ua = lambda fr: min(10.0, 78.125 * max(0.0, best / fr - 1) / (best - 1)) if best > 1 else 0.0
            lo_u, hi_u = ua(fair + 0.005), ua(fair - 0.005); want = round(ua(fair), 2)      # the sheet rounds the fair price
            if best + 1e-9 < take:
                F.append(("BLOCK", f"9am bets {P}", f"{who}: best price ${best:g} is under the take price ${take:g}"))
            if abs(take - 1.05 * fair) > 0.02:
                F.append(("BLOCK", f"9am bets {P}", f"{who}: take price ${take:g} is not 1.05 x the fair price ${fair:g}"))
            if not 1.6 <= fair <= 15:
                F.append(("BLOCK", f"9am bets {P}", f"{who}: fair price ${fair:g} is outside $1.60-$15"))
            if not lo_u - 0.011 <= u <= hi_u + 0.011 or u > 10:
                F.append(("BLOCK", f"9am bets {P}", f"{who}: {u:g}u is not the open book's units at ${best:g} ({want:g}u)"))
            if abs(d - 50 * u) > 1:
                F.append(("BLOCK", f"9am bets {P}", f"{who}: ${d:g} is not {u:g}u at $50"))
            if r.get("price_source") and r["price_source"] != "majors-median":
                F.append(("CHECK", f"9am bets {P}", f"{who}: priced on {r['price_source']}, not the seven majors' prices the rule was tested on"))


def scratched_races(L, P):
    races = {k[0] for k, p in read_prices(L, P).items() if p["scr"]}
    res = f"{L}/{P}-results.txt"
    if os.path.exists(res):
        ran = set()
        for l in open(res):
            m = re.match(r"R(\d+) (.+?)\s+finish (\S+)", l)
            if m:
                ran.add((int(m[1]), norm(m[2])))
                if m[3] == "None":
                    races.add(int(m[1]))
        # a late scratching is simply missing from the results: a runner in the last prices pull that did not run
        # (Kyneton 17 Nov R8: Turnaquid and True Spirit, which is where the founder's 2c came from)
        raced = {k[0] for k in ran}
        races |= {k[0] for k, p in read_prices(L, P).items() if not p["scr"] and k[0] in raced and k not in ran}
    return races


def check_deductions(L, today, F):
    since = (dt.date.fromisoformat(today) - dt.timedelta(days=2)).isoformat()
    for f in sorted(glob.glob(f"{L}/2*-deductions-actual.txt")):
        P = os.path.basename(f)[:-len("-deductions-actual.txt")]
        if P[:10] < since:
            continue
        scr = scratched_races(L, P)
        rows = [pa for pa in ([x.strip() for x in l.split("#")[0].split(",")] for l in open(f)) if len(pa) >= 2 and pa[0].isdigit()]
        bad = [pa for pa in rows if int(pa[0]) not in scr]
        wrong = len(bad) * 2 > len(rows)                 # most of the races have no scratching: the wrong meeting
        for pa in bad:
            F.append(("BLOCK" if wrong else "CHECK", f"deductions {P}", f"R{pa[0]} {pa[1]}c: no scratched runner in that race at "
                      f"this meeting " + ("(is it the right meeting?)" if wrong else "(a late scratching the last pull has not seen?)")))


def check_betmatic(L, today, F):
    since = (dt.date.fromisoformat(today) - dt.timedelta(days=3)).isoformat()
    for f in sorted(glob.glob(f"{L}/2*-ledger.csv")):
        P = os.path.basename(f)[:-len("-ledger.csv")]
        if P[:10] < since:
            continue
        n = sum(1 for r in csv.DictReader(open(f)) for i in (r.get("notification_ids") or "").split("&") if i)
        placed = f.replace("-ledger.csv", "-placed.jsonl")
        if not os.path.exists(placed):
            F.append(("CHECK", f"betmatic {P}", f"{n} orders sent and BetMatic's status never read back: nothing is confirmed placed"))
            continue
        seen, ok, took = set(), 0, 0.0
        for l in open(placed):
            d = json.loads(l)
            seen.add(str(d.get("notification")))
            for r in d.get("records") or []:
                if isinstance(r, dict) and r.get("submit_result") == "Success":
                    ok += 1; took += float(r.get("amount") or 0)
        F.append(("INFO", f"betmatic {P}", f"{n} orders sent, status read for {len(seen)}, {ok} confirmed placed (${took:,.0f})"))
        if len(seen) < n:
            F.append(("CHECK", f"betmatic {P}", f"status was read for {len(seen)} of {n} orders: the rest are unconfirmed"))


def page_settle(L, P):
    """The day page's own settle of the open book, by running betmatic_html.py on a blank page. -> {key: (units, pl)}"""
    with tempfile.TemporaryDirectory() as td:
        page = os.path.join(td, "p.html"); open(page, "w").write("<h1>x</h1>")
        r = subprocess.run([sys.executable, "betmatic_html.py", rr.sheet_for(P, L), P, page, "--results",
                            f"{L}/{P}-results.txt"], cwd=here, capture_output=True, text=True)
        if r.returncode:
            return None
        out = {}
        for m in re.finditer(r"<tr><td><a href='#r(\d+)'>R\d+</a> (.*?)</td><td><b>([\d.]+)u</b></td>.*?<td>([^<]*(?:<b[^>]*>([+-][\d.]+)u</b>)?[^<]*)</td></tr>",
                             open(page).read()):
            if "REAL" in m[2]:
                continue                                  # a real BetMatic fill beside the paper row: not the open book
            out[(int(m[1]), norm(html.unescape(re.sub(r"<[^>]+>", "", m[2]))))] = (float(m[3]), float(m[5]) if m[5] else None)
        return out


def check_settle(L, C, F, today, every=False):
    year = today[:4]
    since = "0" if every else (dt.date.fromisoformat(today) - dt.timedelta(days=SETTLE_DAYS)).isoformat()
    rec = collections.defaultdict(dict)
    for r in rr.open_book():
        if r["date"] >= since:
            rec[f"{r['date']}-{r['meeting']}"][(r["race"], norm(r["horse"]))] = r
    for P in sorted(rec):
        pg = page_settle(L, P)
        if pg is None:
            F.append(("CHECK", f"settle {P}", "the day page's settle could not be run")); continue
        for k in sorted(set(rec[P]) | set(pg)):
            a, b = rec[P].get(k), pg.get(k)
            who = f"R{k[0]} {(a or {}).get('horse', k[1])}"
            if a is None or b is None:
                F.append(("BLOCK", f"settle {P}", f"{who}: in {'the day page' if a is None else 'the running record'} only")); continue
            if abs(a["units"] - b[0]) > 0.011:
                F.append(("BLOCK", f"settle {P}", f"{who}: record {a['units']:.2f}u, day page {b[0]:.2f}u"))
            if b[1] is not None and abs(a["pl"] - b[1]) > 0.011:
                why = "the day page counts a non-runner as a loss, the record voids it" if a["result"] == "void" else "unexplained"
                F.append(("CHECK" if why != "unexplained" else "BLOCK", f"settle {P}",
                          f"{who}: record {a['pl']:+.2f}u, day page {b[1]:+.2f}u ({why})"))
    # the no-Mercer card for each settled day against the record for that day
    by_day = collections.defaultdict(dict)
    for P, bets in rec.items():
        for k, r in bets.items():
            by_day[P[:10]][(P[11:].split("-")[0], k[0], k[1])] = r
    for day, kind, fn, d in cards(C, year):
        if kind != "plain" or day not in by_day or day < FULL_UNITS_FROM:
            continue
        seen = set()
        for m in d.get("meetings", []):
            P = prefix_for(L, day, m["name"])
            if not P:
                continue
            for b in m["bets"]:
                k = (P[11:].split("-")[0], int(b["race"]), norm(b["horse"])); seen.add(k)
                r = by_day[day].get(k)
                who = f"{m['name']} R{b['race']} {b['horse']}"
                if b.get("scr") or (read_prices(L, P).get(k[1:]) or {}).get("scr"):
                    continue                              # scratched: void on both
                if r is None:
                    F.append(("CHECK", f"settle card {fn}", f"{who}: on the card, not in the running record")); continue
                if abs(money(b["units"].rstrip("u")) - r["units"]) > 0.011 or abs(money(b["price"]) - r["open"]) > 0.011:
                    nine = os.path.exists(f"{L}/{P}-9am.csv") and any(
                        (int(x["race"]), norm(x["horse"])) == k[1:] for x in csv.DictReader(open(f"{L}/{P}-9am.csv")))
                    F.append(("INFO" if nine and money(b["units"].rstrip("u")) > r["units"] else "CHECK", f"settle card {fn}",
                              f"{who}: card {b['units']} at {b['price']}, record {r['units']:.2f}u at ${r['open']:g}"
                              + (" (the card adds the 9am fill at the blended price; the record keeps the 9am list apart)" if nine else "")))
        for k, r in by_day[day].items():
            if k not in seen and r["result"] != "void":
                F.append(("CHECK", f"settle card {fn}", f"{k[0]} R{r['race']} {r['horse']} {r['units']:.2f}u: in the running record, not on the card"))


def run(L, C, today, now, settle=True, every=False):
    F = []
    check_sheets(L, today, F)
    check_cards(L, C, today, now, F)
    check_9am(L, today, F)
    check_9am_bets(L, today, F)
    check_deductions(L, today, F)
    check_betmatic(L, today, F)
    if settle:
        check_settle(L, C, F, today, every)
    return F


def selftest():
    """Plant each known miss in a scratch folder and require the flag that names it."""
    with tempfile.TemporaryDirectory() as td:
        L, C = os.path.join(td, "live"), os.path.join(td, "cards"); os.makedirs(L); os.makedirs(C)
        day, P = "2030-01-05", "2030-01-05-testville"
        open(f"{L}/{P}-prices.txt", "w").write("# Testville\n1, Alpha, 3.00, 3.00, fk_open 5.00\n1, Beta, SCR\n2, Gamma, 2.80, 2.80, fk_open 2.80\n"
                                               "2, Delta, SCR, last 9.00, fk_open 8.00\n3, Echo, 6.00, 6.00, fk_open 9.00\n")
        hd = "date,venue,race,jump,number,horse,bet,min_odds,max_odds,stake_units,stake_dollars,order,total_if_all_fire,our_price,note\n"
        open(f"{L}/{P}-betmatic-preopen.csv", "w").write(hd +
            f"{day},Testville,1,,4,Alpha,WIN,4.00,18.00,2.00,100,1 of 1,2.00u,3.00,\n"      # a clean order
            f"{day},Testville,2,,,Gamma,WIN,2.61,30.00,5.00,188,1 of 1,5.00u,2.21,\n"       # no number, $37.50 dollars, over 6x
            f"{day},Testville,3,,7,Echo,WIN,5.00,20.00,1.00,50,1 of 1,1.00u,6.00,\n")       # minimum under our price
        open(f"{L}/{P}-deductions-actual.txt", "w").write("race, cents\n1, 20\n3, 12\n")   # race 3 has no scratching
        open(f"{L}/{P}-9am.csv", "w").write("date,venue,race,number,horse,our_price,blend_price,price_now,take_at_or_above,to_win,stake_a_bookie\n"
                                            f"{day},Testville,1,4,Alpha,2.60,2.22,2.40,2.33,2000,1429\n"   # clean
                                            f"{day},Testville,2,2,Gamma,2.46,2.65,2.70,2.78,2000,800\n")   # under the take price, wrong stake
        open(f"{L}/{P}-9am-v2.csv", "w").write("date,venue,race,number,horse,our_price,avg_now,open,fair_price,best_now,take_at_or_above,"
                                               "also_on_live_list,best_bookies,stake_units,stake_dollars,units_at_take\n"
                                               f"{day},Testville,1,4,Alpha,2.60,2.40,3.00,2.22,2.40,2.33,no,tab,4.52,226,2.94\n"   # clean
                                               f"{day},Testville,3,7,Echo,6.50,6.00,9.00,5.00,6.00,5.25,no,tab,4.00,200,1.00\n")   # 4u, the rule says 3.12u
        open(f"{L}/{P}-betmatic-preopen-ledger.csv", "w").write("label,race,number,horse,min_odds,max_odds,stake,notification_ids,message\n"
                                                                "x-r1-n4-s1,1,4,Alpha,4.00,18.00,100,111,sent\n")
        json.dump({"day": "Saturday", "date": "5 January", "brand": True, "meetings": [{"name": "Testville", "bets": [
            {"race": 2, "horse": "Gamma", "price": "$4.20", "units": "5.00u"},            # $4.20 against $2.80 at the last pull
            {"race": 2, "horse": "Delta", "price": "$8", "units": "1.00u"}]}]},           # scratched and not marked
            open(f"{C}/card_sat05_mercer_now.json", "w"))
        json.dump({"day": "Saturday", "date": "5 January", "brand": False, "meetings": [{"name": "Testville", "bets": [
            {"race": 1, "horse": "Alpha", "price": "$18", "rated": "$3.00", "units": "2.00u"}]}]},   # $18 is not the open ($5)
            open(f"{C}/card_sat05_plain_open.json", "w"))
        for tag, at in (("b", "2030-01-05T07:00"), ("c", "2030-01-05T08:50")):          # 120 minutes old, 10 minutes old
            json.dump({"day": "Saturday", "date": "5 January", "brand": True, "prices_as_at": at, "meetings": [{"name": "Testville",
                       "bets": [{"race": 1, "horse": "Alpha", "price": "$3", "units": "2.00u"}]}]},
                      open(f"{C}/card_sat05{tag}_mercer_now.json", "w"))
        F = run(L, C, day, dt.datetime(2030, 1, 5, 9, 0), settle=False)
        text = "\n".join(f"{a} {b}: {c}" for a, b, c in F)
        want = ["no saddlecloth number", "dollars are not units", "is over 6x", "is not above our price",
                "R3 12c: no scratched runner", "is under the take price", "stake $800 is not",
                "never read back", "no prices_as_at", "card $4.2 against $2.8", "Delta: scratched, and the card does not mark it",
                "card_sat05b_mercer_now.json: prices are 120 minutes old",
                "card $18, Form King's open $5", "Gamma 5.00u is an open-book bet and is not on the card",
                "Echo: 4u is not the open book's units"]
        miss = [w for w in want if w not in text]
        clean_bad = [l for l in text.splitlines() if "R1 20c" in l or ("Alpha" in l and "9am" in l)
                     or ("sat05c" in l and "minutes old" in l) or ("sat05c" in l and "prices_as_at" in l)]
        print(text)
        print(f"\nselftest: {len(want) - len(miss)} of {len(want)} planted misses caught" + (f"; MISSED: {miss}" if miss else "")
              + (f"; FALSE FLAGS on clean rows: {clean_bad}" if clean_bad else "; no flag on the clean rows"))
        return 0 if not miss and not clean_bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day"); ap.add_argument("--enforce", action="store_true"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-settle", action="store_true", help="skip the settle cross-check")
    ap.add_argument("--all", action="store_true", help="cross-check every settled meeting, not only the last week")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    try:
        from zoneinfo import ZoneInfo
        mel = dt.datetime.now(ZoneInfo("Australia/Melbourne"))
    except Exception:                                                   # no tz database on this machine
        mel = dt.datetime.now(dt.timezone(dt.timedelta(hours=11)))      # Melbourne daylight time
    today = a.day or mel.date().isoformat()
    L, C = rr.L, os.path.join(here, "../../branding/mercer-tipping")
    F = run(L, C, today, mel, settle=not a.no_settle, every=a.all)
    n = collections.Counter(x[0] for x in F)
    mode = "enforce" if a.enforce else "observe"
    head = f"## {mel.strftime('%Y-%m-%d %H:%M')} ({mode}), from {today}: {n['BLOCK']} would block, {n['CHECK']} to check, {n['INFO']} notes"
    body = [f"- {lv} {area}: {msg}" for lv, area, msg in sorted(F, key=lambda x: ("BLOCK", "CHECK", "INFO").index(x[0]))]
    print(head); print("\n".join(body) if body else "- clean")
    log = os.path.join(L, "verify-log.md")
    top = "# Verify log\n\nresearch/form_gbm/verify.py, newest first, the last 60 runs. BLOCK = would stop the send or the message once the gate enforces; CHECK = read it; INFO = a note.\n"
    old = open(log).read() if os.path.exists(log) else ""
    blocks = [b for b in re.split(r"(?m)^(?=## )", old) if b.startswith("## ")]
    open(log, "w").write(top + "\n" + "\n".join([head + "\n" + ("\n".join(body) if body else "- clean") + "\n"] + blocks[:59]))
    sys.exit(1 if a.enforce and n["BLOCK"] else 0)


if __name__ == "__main__":
    main()
