"""Send a BetMatic pre-open order file as Market Open bets, cancel them, and check what was placed (14 Oct 2026).
Built from BetMatic's docs (API_NOTES.md). Runs on the founder's always-on machine: Claude builds the order files and
this tool, the founder sends. There is no sandbox in BetMatic's API, so DRY RUN is the default and prints every
payload; nothing is sent without --send.

    set BETMATIC_EMAIL and BETMATIC_PASSWORD in the environment, then:
    (normally run by the fk-betmatic GitHub workflow after the founder approves; it also runs on any machine)
    python betmatic_send.py check                                   bots and sessions running? bookmaker and session IDs
    python betmatic_send.py send ORDERS.csv --unit 25 --session 101 [--bookie TAB] [--send]
    python betmatic_send.py cancel LEDGER.csv [--race 3] [--number 7] [--send]
    python betmatic_send.py status LEDGER.csv                      per-bookmaker placements: odds taken, stake, result
    python betmatic_send.py summary 2026-10-17 [--ledger LEDGER.csv] won / lost / pending that day, against the ledger

send: one Fixed Win, Market Open bet per order row (each price step is its own bet, as BetMatic requires), to ONE
bookmaker and ONE session (target_session, so the stake is never multiplied across accounts), with the row's minimum
odds (check_odds/odds) and maximum odds (check_max_odds/max_odds), stake = stake_units x unit in whole dollars
(a step under $1 is dropped). Every bet carries a unique label; a label already on BetMatic is skipped, so a re-run or a
retry after a timeout cannot double-bet (BetMatic does no duplicate detection). The returned notification IDs go to
a ledger beside the orders (ORDERS-ledger.csv) for cancel and status. Refuses to send if no session shows
bot_running, if no bot machine is connected, if the TAB balance cannot cover the bets (unless --allow-short), if a row
has no saddlecloth number, or if the venue/race is not in BetMatic's race schedule."""
import argparse, csv, json, os, re, sys, time
import requests

API = "https://betmatic.app/api"


class BM:
    def __init__(self):
        r = requests.post(f"{API}/account/login/", json={"email": os.environ["BETMATIC_EMAIL"],
                                                         "password": os.environ["BETMATIC_PASSWORD"],
                                                         "version": "API"}, timeout=30)
        # Tokens are stateless JWTs: a fresh login per run does not disturb the bot's own session. Never call
        # /account/logout/ from here: it disconnects a bot session (API reference, Authentication).
        r.raise_for_status()
        self.h = {"Authorization": f"Token {r.json()['token']}", "Content-Type": "application/json"}

    def get(self, path, **params):
        r = requests.get(f"{API}{path}", headers=self.h, params=params, timeout=30); r.raise_for_status(); return r.json()

    def get_all(self, path, **params):
        """Every page of a paginated list. BetMatic pages at 10-20 rows by default (100 max), an out-of-range page
        returns page 1 rather than an error, and "count" is never below 1, so pages are walked by total_pages and
        rows are counted from "results" (API reference, Overview: Pagination)."""
        first = self.get(path, page=1, page_size=100, **params)
        if not isinstance(first, dict) or "results" not in first:
            return first if isinstance(first, list) else []
        rows = list(first["results"])
        for pg in range(2, int(first.get("total_pages") or 1) + 1):
            rows += list(self.get(path, page=pg, page_size=100, **params).get("results") or [])
        return rows

    def post(self, path, body=None):
        r = requests.post(f"{API}{path}", headers=self.h, json=body or {}, timeout=30)
        return r.status_code, (r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else r.text)


def results(x):
    return x.get("results", x) if isinstance(x, dict) else x


def sessions(bm):
    return bm.get_all("/bookieaccount/")


def bookie_id(bm, name):
    """The bookmaker's numeric id from GET /bookie/names/, matched on its "title" (e.g. "TAB") or its id. Stops if the
    bookmaker is disabled or in maintenance: BetMatic skips bets to a bookmaker in maintenance without an error
    (API reference, Data: Bookmakers)."""
    for b in bm.get_all("/bookie/names/"):
        if str(b.get("title", "")).strip().lower() == name.lower() or str(b.get("id")) == str(name):
            if not b.get("enabled", True) or b.get("maintain"):
                sys.exit(f"bookmaker {b.get('title')} (id {b.get('id')}) is {'in maintenance' if b.get('maintain') else 'disabled'} "
                         "on BetMatic: bets to it would be skipped. Not sending.")
            return str(b["id"])
    sys.exit(f"bookmaker {name!r} not in GET /bookie/names/ (titles: "
             + ", ".join(str(b.get("title")) for b in bm.get_all("/bookie/names/")) + ")")


def readiness(bm):
    """GET /account/readiness/: problems, bot_session_running (connected bot machines), accounts_running (running
    bookmaker sessions) and two notes. A session can read bot_running true while no bot machine is connected, and then
    nothing places, so send checks both (API reference, Bot Diagnostics)."""
    r = bm.get("/account/readiness/")
    return r if isinstance(r, dict) else {}


def check(a):
    bm = BM()
    for s in sessions(bm):
        print(f"session {s.get('id')}: {s.get('display_name')} bookie={s.get('bookie')} bot_running={s.get('bot_running')} "
              f"balance ${float(s.get('balance') or 0):,.2f} (bonus ${float(s.get('bonus_balance') or 0):,.2f}) as at {s.get('update_time')}")
    r = readiness(bm)
    print(f"readiness: {r.get('problems')} problem(s), {r.get('bot_session_running')} bot machine(s) connected, "
          f"{r.get('accounts_running')} session(s) running. {r.get('bot_session_note', '')} {r.get('bot_version_note', '')}".rstrip())
    for x in bm.get("/account/connect_activity/", page_size=5).get("results", [])[:5]:
        print(f"  bot {x.get('session_nickname')}: {x.get('note')} at {x.get('created_at')}")
    want = getattr(a, "bookie", "TAB")
    tab = [b for b in bm.get_all("/bookie/names/") if str(b.get("title", "")).strip().lower() == want.lower()]
    print("bookmaker:", tab[0] if tab else f"{want!r} not found by title")


def label(o, step, tag=""):
    # tag: a resend after BetMatic has already fired (and so will not cancel) the first set; the fired labels stay live
    # and would block the duplicate check, so the resend carries its own (16 Oct 2026, Avoca fired before the TAB priced)
    return f"fk-{o['date']}-{o['venue'].lower().replace(' ', '')}-r{o['race']}-n{o['number']}-s{step}" + (f"-{tag}" if tag else "")


def send(a):
    rows = list(csv.DictReader(open(a.orders)))
    bad = [r for r in rows if not r.get("number") and not r.get("horse")]
    if bad:
        sys.exit(f"{len(bad)} rows have no saddlecloth number and no horse (rebuild the order file with --numbers)")
    bets, step = [], {}
    for o in rows:
        k = (o["race"], o["number"]); step[k] = step.get(k, 0) + 1
        stake = round(float(o["stake_units"]) * a.unit)
        if stake < 1:
            continue
        bets.append((label(o, step[k], getattr(a, "tag", "")), o, {
            "type": "Fixed Wager", "sports": "RACING", "competition": o["venue"].upper(), "code": "Galloping",
            "event_number": int(o["race"]), "market": "Fixed Win", "selection": str(o["number"]), "stake": stake,
            "check_odds": True, "odds": float(o["min_odds"]),
            "check_max_odds": bool(o.get("max_odds")), **({"max_odds": float(o["max_odds"])} if o.get("max_odds") else {}),
            "is_market_open": not a.now, "max_attempts": a.attempts, "delay_between_attempts": 1,
            "allow_double_bets": False, "take_sp": False, "label": None}))
        if getattr(a, "best_price", False):
            # best bookie price (21 Oct 2026, founder: "do top bookie price"): High Odds First puts the whole stake with
            # the highest-priced bookmaker and moves down only if it is rejected or not filled (support, 18 Oct). It is
            # a standard bet only (not Market Open), works from one total, and spans every running session.
            b = bets[-1][2]; b.update(type="High Odds First", total_wager=b["stake"])
    total = sum(b[2]["stake"] for b in bets)
    print(f"{len(bets)} bets, ${total:,} if every one fired, unit ${a.unit}")
    # dry run (21 Oct 2026): logs in and checks every bet against BetMatic's race schedule too (venue, race, the
    # number at that name), so a dry run proves the order would land on the right horse; it only stops short of posting
    if not str(a.session).isdigit():
        sys.exit("--session must be the numeric session ID from 'check': BetMatic ignores a non-numeric target_session "
                 "and sends the bet to EVERY session (API reference, Create a Bet)")
    bm = BM()
    mine = [s for s in sessions(bm) if str(s.get("id")) == str(a.session)]
    if not mine:
        sys.exit(f"session {a.session} not found on this account (run 'check')")
    rd = readiness(bm)
    # The session's bot_running is a SNAPSHOT (as at its update_time) and can read false for hours while the bot is up:
    # on 30-31 Oct 2026 it blocked every send from Friday 2:41pm to Saturday 10:42am while the founder's bot was running
    # the whole time, and missed Mornington, Traralgon, Flemington R2-R6 and Ballarat R4/R5/R7 at the open. The live
    # signals are readiness (bot machines connected, sessions running), so the snapshot is only a warning now.
    if not mine[0].get("bot_running"):
        print(f"WARNING: session {a.session} snapshot says bot_running false (as at {mine[0].get('update_time')}); "
              f"readiness says {rd.get('bot_session_running')} bot machine(s) connected, {rd.get('accounts_running')} "
              f"session(s) running", flush=True)
        if not int(rd.get("accounts_running") or 0):
            sys.exit(f"session {a.session} is not running (snapshot false and readiness shows no session running): "
                     "start the bot and the session first")
    live = mine
    if not int(rd.get("bot_session_running") or 0):
        sys.exit("no bot machine is connected (GET /account/readiness/): the bets would queue and never place. "
                 "Start the BetMatic bot on the always-on machine first")
    # balance is the session's real-money balance (bonus is not used: use_bonus is off). A Market Open bet that finds
    # no money fails at TAB, so a short balance means the later bets of the day fail. Stale by up to the update_time.
    bal = float(live[0].get("balance") or 0)
    if bal < total:
        msg = (f"TAB balance ${bal:,.2f} (as at {live[0].get('update_time')}) is below the ${total:,} these bets "
               f"need if every one fires")
        # Warning only (15 Oct 2026): BetMatic read the TAB session at $0.00 for an hour after the founder loaded $5
        # into that same account, so its balance is not a reliable gate. TAB itself refuses a bet it cannot cover,
        # and status shows that as FAILED with the bot's own log line.
        print("WARNING:", msg, "(BetMatic's TAB balance reading has been unreliable; sending, TAB will refuse what it cannot cover)")
    bid = bookie_id(bm, a.bookie)
    # A bet names the venue and race number; without start_time BetMatic takes the NEXT race at that venue and number,
    # and the schedule runs up to 5-6 days ahead (API reference: Race Schedule; Create a Bet). So each bet is matched to
    # the schedule entry on the order's own date and pinned with that race's startTime, copied as BetMatic gives it.
    # A bet is skipped if that race is not in the schedule, its saddlecloth is no longer running (scratched runners
    # leave "runners"), or the name at that number is not our horse.
    sched = bm.get_all("/competition/namecodes/")
    on_day = {}
    for c in sched:
        if isinstance(c, dict) and c.get("code") == "Galloping":
            on_day[(str(c.get("name", "")).upper(), int(c.get("event_number", 0)), str(c.get("startTime", ""))[:10])] = c
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())

    def race_problem(o, body):
        c = on_day.get((body["competition"], body["event_number"], o["date"]))
        if c is None:
            return f"{body['competition']} R{body['event_number']} on {o['date']} is not in BetMatic's race schedule"
        nums = [x.strip() for x in str(c.get("runners", "")).split(",")]
        names = str(c.get("runner_names", "")).split("#&#")
        if body["selection"] in ("", "0"):
            # number left blank (a copied tip names only the horse, 21 Oct 2026): take it from BetMatic's own field
            hit = [n for n, nm in zip(nums, names) if norm(nm) == norm(o["horse"])] if len(names) == len(nums) else []
            if len(hit) != 1:
                return (f"{o['horse']!r} is not (uniquely) in BetMatic's field for {body['competition']} R{body['event_number']}: "
                        f"runners {nums}, names {names}")
            body["selection"] = o["number"] = hit[0]; print(f"{o['horse']}: No. {hit[0]} in BetMatic's field")
        if body["selection"] not in nums:
            return f"No. {body['selection']} is not running (scratched) in BetMatic's schedule"
        if len(names) == len(nums) and norm(names[nums.index(body["selection"])]) != norm(o["horse"]):
            return f"No. {body['selection']} is {names[nums.index(body['selection'])]!r} on BetMatic, not {o['horse']!r}"
        body["start_time"] = c["startTime"]
        return None
    ledger_fn = a.orders.replace(".csv", "-ledger.csv"); new = not os.path.exists(ledger_fn)
    skipped = []   # labels already on BetMatic (22 Oct 2026: 10 of 13 Flemington resends were skipped with one quiet line each)
    with open(ledger_fn if a.send else os.devnull, "a", newline="") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["label", "race", "number", "horse", "min_odds", "max_odds", "stake", "notification_ids", "message"])
        for lab, o, body in bets:
            prob = race_problem(o, body)
            if prob:
                print(f"SKIP {lab}: {prob}"); w.writerow([lab, o["race"], o["number"], o["horse"], o["min_odds"], o.get("max_odds", ""), body["stake"], "", "SKIPPED: " + prob]); continue
            if not a.send:
                shown = dict(body, label=lab)
                if not getattr(a, "best_price", False): shown.update(bookies=f"<{a.bookie}>", target_session=str(a.session))
                print("DRY RUN, would send:", json.dumps(shown)); continue
            # exact label only: the docs do not say whether ?label= matches exactly or as part of a longer label
            # a cancelled notification keeps its label, so it does not count as already sent (15 Oct 2026: Horsham was
            # cancelled to re-price after the gear changes, and the re-send would otherwise have skipped every bet)
            if any(isinstance(n, dict) and n.get("label") == lab and not n.get("is_canceled")
                   for n in results(bm.get("/notification/", label=lab, page_size=100))):
                print(f"SKIP {lab}: already on BetMatic"); skipped.append(lab); continue
            body.update(label=lab) if getattr(a, "best_price", False) else body.update(label=lab, bookies=bid, target_session=str(a.session))
            code, resp = bm.post("/notification/create/", body)
            msg = resp.get("message", "") if isinstance(resp, dict) else str(resp)
            ids = str(resp.get("id", "")) if isinstance(resp, dict) else ""
            ok = code == 200 and ids and "no signal" not in msg.lower()
            print(f"{'OK ' if ok else 'FAIL'} {lab} ${body['stake']} min {body['odds']} -> {code} {msg} {ids}")
            w.writerow([lab, o["race"], o["number"], o["horse"], o["min_odds"], o.get("max_odds", ""), body["stake"], ids, msg])
            time.sleep(0.2)
    if skipped:
        print(f"\n*** {len(skipped)} of {len(bets)} bets NOT SENT: their labels are already on BetMatic "
              f"(a previous send of this file). To send them again, re-run with a new tag (eg --tag b). ***")
    print("ledger:", ledger_fn if a.send else "(dry run: nothing sent, no ledger written; add --send to send)")


def cancel(a):
    rows = [r for r in csv.DictReader(open(a.ledger)) if (not a.race or r["race"] == str(a.race)) and (not a.number or r["number"] == str(a.number))]
    ids = [i for r in rows for i in r["notification_ids"].split("&") if i]
    print(f"{len(ids)} notifications to cancel ({len(rows)} bets)")
    if not a.send:
        print("DRY RUN:", ids); return
    bm = BM()
    for i in ids:
        code, resp = bm.post(f"/notification/{i}/cancel/")
        print(i, code, resp)


def pending(a):
    """Before the open: is every order in the ledger waiting on BetMatic? GET /notification/scheduled/ lists pending
    Market Open and scheduled bets (a plain array, last 24 hours only); a ledger id missing from it has fired, been
    cancelled, or never registered, and is named so it can be resent while there is time."""
    bm = BM(); got = bm.get("/notification/scheduled/"); got = got if isinstance(got, list) else results(got)
    live = {str(n.get("id")): n for n in got if isinstance(n, dict) and not n.get("is_canceled")}
    rows = [r for r in csv.DictReader(open(a.ledger)) if r.get("notification_ids")]
    ok = missing = 0
    for r in rows:
        for i in r["notification_ids"].split("&"):
            if i in live:
                ok += 1
                n = live[i]
                # 19 Oct 2026, Geelong R8/R9: orders that came out is_draft false before their race opened never fired
                # when TAB opened it. A Market Open order should sit in draft until the open; flag any that does not.
                if n.get("is_market_open") and n.get("is_draft") is False and not n.get("triggered_at"):
                    print(f"NOT DRAFT {r['label']} (id {i}): BetMatic treats this market as already open but has not fired it; "
                          "check TAB, cancel and resend if the race has not opened")
            else:
                missing += 1; print(f"NOT PENDING {r['label']} (id {i}): fired, cancelled or never registered")
    print(f"{ok} pending, {missing} not pending, {len(live)} pending on BetMatic in all")


def inspect(a):
    """Read-only: what BetMatic has stored for each order in the ledger (GET /notification/?label=, the instruction as
    BetMatic holds it) and the race it linked the order to (GET /notification/{id}/race/detail/). Added 19 Oct 2026
    after Geelong R5's orders fired at TAB's open while R8 and R9's never reached the bot: compare the fired race's
    orders with the others field by field. --race limits it to one race."""
    bm = BM(); shown = set()
    for r in csv.DictReader(open(a.ledger)):
        if a.race and r["race"] != str(a.race):
            continue
        for i in r["notification_ids"].split("&"):
            if not i:
                continue
            got = bm.get("/notification/", label=r["label"])
            rows = [n for n in (got if isinstance(got, list) else results(got)) if isinstance(n, dict) and n.get("label") == r["label"]]
            n = rows[0] if rows else {}
            tip = n.get("tip") or {}
            comp = tip.get("competition") if isinstance(tip.get("competition"), dict) else {"name": tip.get("competition")}
            if r["race"] not in shown:   # the full stored record once per race, so the fields can be compared
                shown.add(r["race"])
                print(f"--- R{r['race']} full record for {r['label']}:\n{json.dumps(n, default=str)[:2500]}")
            keep = {k: n.get(k) for k in ("id", "is_market_open", "is_canceled", "is_triggered", "status", "created_at",
                                          "scheduled_time", "market_open_time", "triggered_at") if k in n}
            print(f"R{r['race']} {r['label']} #{i}: {comp} event {tip.get('event_number')} sel {tip.get('selection')} "
                  f"start {tip.get('start_time') or tip.get('event_time')} {keep}")
            try:
                d = bm.get(f"/notification/{i}/race/detail/")
                print("    race detail:", json.dumps(d, default=str)[:600])
            except requests.HTTPError as e:
                print(f"    race detail: unavailable ({e})")


def bot_logs(bm, nid):
    """The bot's own log lines for one bet (GET /bot/logs/{notification_id}/, grouped by bot instance). Empty when the
    bot never saw the bet, which is itself the diagnosis (API reference, Bot Diagnostics)."""
    try:
        got = bm.get(f"/bot/logs/{nid}/")
    except requests.HTTPError as e:
        print(f"    bot logs: unavailable ({e})"); return
    lines = [f"{g.get('bot_instance')}: {redact_account(l.get('log'))}" for g in (got if isinstance(got, list) else [])
             for l in g.get("logs") or []]
    print("    bot logs: " + (" | ".join(lines[-6:]) if lines else "none (the bot never received this bet)"))


def redact_account(line):
    """The bot names the bookmaker account holder ("TAB, <full name> : Skipped ..."); Actions logs on this repo are
    public, so the name is replaced before printing (27 Oct 2026: a diagnose run printed it)."""
    return re.sub(r"\b([A-Za-z0-9 ]{2,20}), [^:|]{2,60} :", r"\1, [account holder] :", str(line))


def summary(a):
    """GET /bet/summary/: won, lost and pending bets for one Sydney day (date_to is exclusive, so the day after), next
    to the ledger's count of bets sent, so a bet that never reached BetMatic shows as a gap."""
    from datetime import date, timedelta
    d = date.fromisoformat(a.date)
    got = BM().get("/bet/summary/", date_from=str(d), date_to=str(d + timedelta(days=1)), code="Galloping")
    print(f"{a.date}: won {got.get('won')}, lost {got.get('lost')}, pending {got.get('pending')} (all BetMatic racing bets that day)")
    if a.ledger:
        sent = sum(1 for r in csv.DictReader(open(a.ledger)) for i in r["notification_ids"].split("&") if i)
        print(f"ledger: {sent} bets sent; BetMatic accounts for {sum(int(got.get(k) or 0) for k in ('won', 'lost', 'pending'))}")


def status(a):
    """Every order's placement at TAB, from the bet records (GET /bet/notification/{id}/ -> "bets"): amount TAB took,
    the odds taken (current_odds), submit_result / submit_error, status and profit. Flags a bet TAB took for LESS than
    we asked (reduced offer), a failed submission, and a fill below our minimum odds (should never happen)."""
    bm = BM(); out = a.ledger.replace("-ledger.csv", "-placed.jsonl")
    tot_ask = tot_took = 0.0; n_cut = n_fail = 0
    deds = {}   # race -> (cents, horse): TAB's own deduction on our settled bets, filed for settling (15 Oct 2026)
    with open(out, "a") as fh:
        for r in csv.DictReader(open(a.ledger)):
            for i in r["notification_ids"].split("&"):
                if not i: continue
                got = bm.get(f"/bet/notification/{i}/")
                # {"bets": [...]} per the API's worked examples; status is "" until settled as Won / Lost / Refund
                recs = got.get("bets", results(got)) if isinstance(got, dict) else got
                ded = got.get("average_deduction_percentage") if isinstance(got, dict) else None   # TAB's actual scratching deduction
                fh.write(json.dumps({"label": r["label"], "notification": i, "deduction": ded, "records": recs}) + "\n")
                recs = [x for x in (recs if isinstance(recs, list) else [recs]) if isinstance(x, dict)]
                ask = float(r["stake"] or 0); tot_ask += ask
                if not recs:
                    print(f"{r['label']} #{i}: no placement yet (waiting for the open, or nothing was sent)"); bot_logs(bm, i); continue
                if ded not in (None, "") and any(x.get("status") for x in recs):
                    try:
                        c = round(float(str(ded).rstrip("%")))
                        if c > deds.get(r["race"], (-1, ""))[0]: deds[r["race"]] = (c, r["horse"])
                    except ValueError:
                        pass
                for x in recs:
                    took = float(x.get("amount") or 0) if x.get("submit_result") == "Success" else 0.0; tot_took += took
                    flag = []
                    if x.get("submit_result") != "Success":
                        flag.append(f"FAILED: {x.get('submit_error')}"); n_fail += 1
                    elif took + 0.01 < ask:
                        flag.append(f"REDUCED: asked ${ask:g}, TAB took ${took:g}"); n_cut += 1
                    odds = x.get("current_odds")
                    if odds and r.get("min_odds") and float(odds) + 1e-9 < float(r["min_odds"]):
                        flag.append(f"BELOW MIN ODDS {r['min_odds']}")
                    print(f"{r['label']} #{i}: ${took:g} @ {odds} {x.get('status') or 'unsettled'} {x.get('profit', '')} deduction {ded} {'; '.join(flag)}")
                    if x.get("submit_result") != "Success":
                        bot_logs(bm, i)
    print(f"asked ${tot_ask:,.0f}, TAB took ${tot_took:,.0f}; {n_cut} reduced, {n_fail} failed. raw records: {out}")
    if deds:
        # DAYPREFIX-deductions-actual.txt is what deductions.py, betmatic_fills.py and the forward test settle with. A race
        # already in the file (typed by the founder from his account) is left as he wrote it.
        m = re.match(r"^(\d{4}-\d{2}-\d{2}-[a-z0-9-]+?)-(?:betmatic|test)", os.path.basename(a.ledger))
        if not m:
            print("deductions not filed: cannot read the meeting from", a.ledger); return
        fn = os.path.join(os.path.dirname(a.ledger), m.group(1) + "-deductions-actual.txt")
        have = set()
        if os.path.exists(fn):
            have = {l.split(",")[0].strip() for l in open(fn) if l[:1].isdigit()}
        new = [(rc, c, h) for rc, (c, h) in sorted(deds.items(), key=lambda kv: int(kv[0])) if rc not in have]
        if new:
            fresh = not os.path.exists(fn)
            with open(fn, "a") as fh:
                if fresh:
                    fh.write("# deductions TAB applied to our settled bets, read from BetMatic (average_deduction_percentage). Cents in the dollar, win.\n")
                for rc, c, h in new:
                    fh.write(f"{rc}, {c}  # {h} (BetMatic)\n")
            print(f"deductions filed in {fn}: " + ", ".join(f"R{rc} {c}c" for rc, c, h in new))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    s = sp.add_parser("send"); s.add_argument("orders"); s.add_argument("--unit", type=float, required=True, help="dollars a unit")
    s.add_argument("--session", required=True, help="the TAB session ID from 'check'"); s.add_argument("--bookie", default="TAB")
    s.add_argument("--attempts", type=int, default=60, help="placement retries a second apart if the first fails at the open (BetMatic's own default is 60)")
    s.add_argument("--now", action="store_true", help="place now on a market that is already up (a test bet), not as a Market Open bet")
    s.add_argument("--best-price", action="store_true", help="with --now: High Odds First across every running session (the top bookie price)")
    s.add_argument("--allow-short", action="store_true", help="send even if the TAB balance is below the total stake")
    s.add_argument("--tag", default="", help="suffix for every label, for a resend after the first set already fired (e.g. b)")
    s.add_argument("--send", action="store_true")
    c = sp.add_parser("cancel"); c.add_argument("ledger"); c.add_argument("--race"); c.add_argument("--number"); c.add_argument("--send", action="store_true")
    t = sp.add_parser("status"); t.add_argument("ledger")
    pn = sp.add_parser("pending"); pn.add_argument("ledger")
    ins = sp.add_parser("inspect"); ins.add_argument("ledger"); ins.add_argument("--race")
    sm = sp.add_parser("summary"); sm.add_argument("date", help="Sydney day, YYYY-MM-DD"); sm.add_argument("--ledger")
    a = ap.parse_args(); {"check": check, "send": send, "cancel": cancel, "status": status, "pending": pending,
                          "summary": summary, "inspect": inspect}[a.cmd](a)
