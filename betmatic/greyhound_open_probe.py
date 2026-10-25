"""TAB's opening price on every Victorian greyhound runner, via BetMatic's Market Open trigger and an instruction that can
never fill (rules and safety in greyhound/open_probe.py). DRY RUN is the default: nothing is sent without --send.

    python betmatic/greyhound_open_probe.py send --session 101 [--days 3] [--limit 0] [--state VIC] [--send]
    python betmatic/greyhound_open_probe.py collect

send:    one instruction per runner in every upcoming race not already in the ledger (data/greyhound/probe/ledger.csv);
         --limit N sends only the first N (the first live test is one race). Refuses without a connected bot machine or
         a running numeric session, and stops at the first refusal from BetMatic so a bad field cannot repeat 400 times.
collect: reads BetMatic's records for every ledger row not yet settled into opens.csv (one row per runner: TAB's
         price when BetMatic fired, when, and whether that can count as an open). Stops loudly on any STAKED row.
"""
import argparse, csv, json, os, sys, time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from betmatic_send import BM, bookie_id, readiness, results, sessions                        # noqa: E402
from greyhound.open_probe import DERIVED_FIELDS, derive, payload, plan                      # noqa: E402

LEDGER_FIELDS = ["label", "date", "venue", "race", "number", "runner", "start_time", "sent_at", "notification_id",
                 "message"]


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def send(a, ledger):
    bm = BM()
    done = {r["label"] for r in read_csv(ledger) if r.get("notification_id")}
    todo = plan(bm.get_all("/competition/namecodes/"), datetime.now(timezone.utc), a.state, timedelta(days=a.days), done)
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(todo)} instructions to send ({len(done)} already in the ledger); each min ${1000:,} / max $1.01, $1, TAB, "
          "one attempt: refused at the open by design")
    for p in todo[:3]:
        print("  e.g.", json.dumps({k: p[k] for k in ("label", "venue", "race", "number", "runner", "start_time")}))
    if not todo:
        return 0
    tab = bookie_id(bm, "TAB")
    if not any(str(s.get("id")) == str(a.session) and s.get("bot_running") for s in sessions(bm)):
        sys.exit(f"session {a.session} is not running: start the bot and its TAB session first")
    if not int(readiness(bm).get("bot_session_running") or 0):
        sys.exit("no bot machine connected: the instructions would never reach a bot")
    if not a.send:
        print("DRY RUN, first payload:", json.dumps(payload(todo[0], tab, a.session)))
        return 0
    new = not os.path.exists(ledger)
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    sent = 0
    with open(ledger, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
        if new:
            w.writeheader()
        for p in todo:
            if any(isinstance(n, dict) and n.get("label") == p["label"] and not n.get("is_canceled")
                   for n in results(bm.get("/notification/", label=p["label"], page_size=100))):
                print(f"SKIP {p['label']}: already on BetMatic"); continue
            at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            code, resp = bm.post("/notification/create/", payload(p, tab, a.session))
            msg = resp.get("message", "") if isinstance(resp, dict) else str(resp)
            nid = str(resp.get("id", "")) if isinstance(resp, dict) else ""
            ok = code == 200 and nid and "no signal" not in msg.lower()
            w.writerow({**{k: p[k] for k in ("label", "date", "venue", "race", "number", "runner", "start_time")},
                        "sent_at": at, "notification_id": nid if ok else "", "message": f"{code} {msg}"[:200]})
            fh.flush()
            if not ok:
                sys.exit(f"STOPPED at {p['label']}: BetMatic answered {code} {str(resp)[:300]}. Nothing after it was sent.")
            sent += 1; time.sleep(0.2)
    print(f"sent {sent}; ledger {ledger}")
    return 0


def collect(a, ledger, out):
    bm = BM()
    rows = [r for r in read_csv(ledger) if r.get("notification_id")]
    have = {r["label"]: r for r in read_csv(out)}
    staked = []
    for r in rows:
        if have.get(r["label"], {}).get("status") in ("refused", "other", "STAKED"):
            continue
        recs = []
        for nid in r["notification_id"].split("&"):
            got = bm.get(f"/bet/notification/{nid}/")
            recs += (got.get("bets") or []) if isinstance(got, dict) else []
        d = derive(r, recs)
        have[r["label"]] = d
        if d["status"] == "STAKED":
            staked.append(d)
        time.sleep(0.1)
    with open(out + ".part", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=DERIVED_FIELDS); w.writeheader()
        w.writerows(sorted(have.values(), key=lambda x: (x["date"], x["venue"], int(x["race"]), x["number"])))
    os.replace(out + ".part", out)
    from collections import Counter
    c = Counter(v["status"] for v in have.values())
    known = sum(1 for v in have.values() if str(v["open_known"]) == "True")
    print(f"{len(have)} runners: {dict(c)}; usable as an open: {known}")
    if staked:
        sys.exit("MONEY WENT ON, which must never happen: " + "; ".join(f"{s['label']} ${s['amount']}" for s in staked))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default="data/greyhound/probe")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("send"); s.add_argument("--session", required=True); s.add_argument("--days", type=float, default=3)
    s.add_argument("--limit", type=int, default=0); s.add_argument("--state", default="VIC")
    s.add_argument("--send", action="store_true")
    sp.add_parser("collect")
    a = ap.parse_args()
    led, opens = os.path.join(a.dir, "ledger.csv"), os.path.join(a.dir, "opens.csv")
    sys.exit(send(a, led) if a.cmd == "send" else collect(a, led, opens))
