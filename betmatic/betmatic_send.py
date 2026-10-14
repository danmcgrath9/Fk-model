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

send: one Fixed Win, Market Open bet per order row (each price step is its own bet, as BetMatic requires), to ONE
bookmaker and ONE session (target_session, so the stake is never multiplied across accounts), with the row's minimum
odds (check_odds/odds) and maximum odds (check_max_odds/max_odds), stake = stake_units x unit in whole dollars
(a step under $1 is dropped). Every bet carries a unique label; a label already on BetMatic is skipped, so a re-run or a
retry after a timeout cannot double-bet (BetMatic does no duplicate detection). The returned notification IDs go to
a ledger beside the orders (ORDERS-ledger.csv) for cancel and status. Refuses to send if no session shows
bot_running, if a row has no saddlecloth number, or if the venue/race is not in BetMatic's race schedule."""
import argparse, csv, json, os, sys, time
import requests

API = "https://betmatic.app/api"


class BM:
    def __init__(self):
        r = requests.post(f"{API}/account/login/", json={"email": os.environ["BETMATIC_EMAIL"],
                                                         "password": os.environ["BETMATIC_PASSWORD"]}, timeout=30)
        r.raise_for_status()
        self.h = {"Authorization": f"Token {r.json()['token']}", "Content-Type": "application/json"}

    def get(self, path, **params):
        r = requests.get(f"{API}{path}", headers=self.h, params=params, timeout=30); r.raise_for_status(); return r.json()

    def post(self, path, body=None):
        r = requests.post(f"{API}{path}", headers=self.h, json=body or {}, timeout=30)
        return r.status_code, (r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else r.text)


def results(x):
    return x.get("results", x) if isinstance(x, dict) else x


def sessions(bm):
    return results(bm.get("/bookieaccount/"))


def bookie_id(bm, name):
    for b in results(bm.get("/bookie/names/")):
        if str(b.get("name", "")).strip().lower() == name.lower() or str(b.get("id")) == str(name):
            return str(b["id"])
    sys.exit(f"bookmaker {name!r} not in GET /bookie/names/")


def check(a):
    bm = BM()
    for s in sessions(bm):
        print(f"session {s.get('id')}: {s.get('display_name')} bookie={s.get('bookie') or s.get('bookie_name')} bot_running={s.get('bot_running')}")
    print("readiness:", json.dumps(bm.get("/account/readiness/"))[:600])


def label(o, step):
    return f"fk-{o['date']}-{o['venue'].lower().replace(' ', '')}-r{o['race']}-n{o['number']}-s{step}"


def send(a):
    rows = list(csv.DictReader(open(a.orders)))
    bad = [r for r in rows if not r.get("number")]
    if bad:
        sys.exit(f"{len(bad)} rows have no saddlecloth number (rebuild the order file with --numbers)")
    bets, step = [], {}
    for o in rows:
        k = (o["race"], o["number"]); step[k] = step.get(k, 0) + 1
        stake = round(float(o["stake_units"]) * a.unit)
        if stake < 1:
            continue
        bets.append((label(o, step[k]), o, {
            "type": "Fixed Wager", "sports": "RACING", "competition": o["venue"].upper(), "code": "Galloping",
            "event_number": int(o["race"]), "market": "Fixed Win", "selection": str(o["number"]), "stake": stake,
            "check_odds": True, "odds": float(o["min_odds"]),
            "check_max_odds": bool(o.get("max_odds")), **({"max_odds": float(o["max_odds"])} if o.get("max_odds") else {}),
            "is_market_open": True, "max_attempts": a.attempts, "delay_between_attempts": 1,
            "allow_double_bets": False, "take_sp": False, "label": None}))
    total = sum(b[2]["stake"] for b in bets)
    print(f"{len(bets)} bets, ${total:,} if every one fired, unit ${a.unit}")
    if not a.send:
        for lab, o, body in bets:
            body["label"] = lab; body["bookies"] = f"<{a.bookie}>"; body["target_session"] = str(a.session)
            print(json.dumps(body))
        print("DRY RUN: nothing sent. Add --send to send.")
        return
    bm = BM()
    live = [s for s in sessions(bm) if str(s.get("id")) == str(a.session) and s.get("bot_running")]
    if not live:
        sys.exit(f"session {a.session} is not running (bot_running false): start the bot and the session first")
    bid = bookie_id(bm, a.bookie)
    sched = results(bm.get("/competition/namecodes/"))
    known = {(str(c.get("name", "")).upper(), str(c.get("code")), int(c.get("event_number", 0))) for c in sched if isinstance(c, dict)}
    ledger_fn = a.orders.replace(".csv", "-ledger.csv"); new = not os.path.exists(ledger_fn)
    with open(ledger_fn, "a", newline="") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["label", "race", "number", "horse", "min_odds", "max_odds", "stake", "notification_ids", "message"])
        for lab, o, body in bets:
            if known and (body["competition"], "Galloping", body["event_number"]) not in known:
                print(f"SKIP {lab}: {body['competition']} R{body['event_number']} not in BetMatic's race schedule"); continue
            if results(bm.get("/notification/", label=lab)):
                print(f"SKIP {lab}: already on BetMatic"); continue
            body.update(label=lab, bookies=bid, target_session=str(a.session))
            code, resp = bm.post("/notification/create/", body)
            msg = resp.get("message", "") if isinstance(resp, dict) else str(resp)
            ids = str(resp.get("id", "")) if isinstance(resp, dict) else ""
            ok = code == 200 and ids and "no signal" not in msg.lower()
            print(f"{'OK ' if ok else 'FAIL'} {lab} ${body['stake']} min {body['odds']} -> {code} {msg} {ids}")
            w.writerow([lab, o["race"], o["number"], o["horse"], o["min_odds"], o.get("max_odds", ""), body["stake"], ids, msg])
            time.sleep(0.2)
    print("ledger:", ledger_fn)


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


def status(a):
    bm = BM(); out = a.ledger.replace("-ledger.csv", "-placed.jsonl")
    with open(out, "a") as fh:
        for r in csv.DictReader(open(a.ledger)):
            for i in r["notification_ids"].split("&"):
                if not i: continue
                recs = results(bm.get(f"/bet/notification/{i}/"))
                fh.write(json.dumps({"label": r["label"], "notification": i, "records": recs}) + "\n")
                for x in (recs if isinstance(recs, list) else [recs]):
                    print(r["label"], i, {k: x.get(k) for k in ("submit_result", "status", "odds", "stake", "profit") if isinstance(x, dict)})
    print("raw records:", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    s = sp.add_parser("send"); s.add_argument("orders"); s.add_argument("--unit", type=float, required=True, help="dollars a unit")
    s.add_argument("--session", required=True, help="the TAB session ID from 'check'"); s.add_argument("--bookie", default="TAB")
    s.add_argument("--attempts", type=int, default=10, help="placement retries a second apart if the first fails at the open")
    s.add_argument("--send", action="store_true")
    c = sp.add_parser("cancel"); c.add_argument("ledger"); c.add_argument("--race"); c.add_argument("--number"); c.add_argument("--send", action="store_true")
    t = sp.add_parser("status"); t.add_argument("ledger")
    a = ap.parse_args(); {"check": check, "send": send, "cancel": cancel, "status": status}[a.cmd](a)
