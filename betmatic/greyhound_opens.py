"""Record every bookmaker's opening price on Victorian greyhound races, from our own BetMatic bot (founder, 25 Oct
2026: "let's record it ourselves from now on"). Read-only: odds requests only, never a bet. Rules in greyhound/opens.py.

    python betmatic/greyhound_opens.py [--hours 5.5] [--state VIC] [--every 180] [--open-every 1200]
           [--ahead 30] [--out data/greyhound/opens]

Needs BETMATIC_EMAIL / BETMATIC_PASSWORD in the environment, WebSocket access (enabled 18 Oct), and the bot machine
running with its TAB session online: the prices are read by OUR bot from OUR accounts, so only bookmakers we hold a
running session with appear, and nothing is recorded while the bot is off.

ONE REQUEST AT A TIME. An odds answer does not say which race it is for (the gallops logs: an answer arrives 0-2s
after its request, sometimes 37s late, sometimes twice). So a request is sent, and an answer counts only if it arrives
while that request is the only one open and within --wait seconds; anything else is logged as unattributed and never
filed against a race. Slower than firing every race at once, and the only way the prices land on the right race.

Writes, per race day, opens-YYYY-MM-DD.csv.gz (merged with any earlier run that day: an open caught earlier is never
replaced) and a raw log of every message for this run, raw-<run start>.jsonl.gz."""
import argparse, csv, gzip, json, os, queue, sys, threading, time
from collections import Counter
from datetime import datetime, timedelta, timezone

import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from betmatic_send import BM                                                   # noqa: E402
from greyhound.opens import ROW_FIELDS, SYDNEY, RaceBook, merge_rows, select_races   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--hours", type=float, default=5.5, help="how long to run")
ap.add_argument("--state", default="VIC")
ap.add_argument("--every", type=int, default=180, help="seconds between polls of a race TAB has not opened")
ap.add_argument("--open-every", type=int, default=1200, help="seconds between polls once TAB is open")
ap.add_argument("--ahead", type=float, default=30, help="hours before the jump to start polling a race")
ap.add_argument("--wait", type=float, default=20, help="seconds to wait for an answer")
ap.add_argument("--out", default="data/greyhound/opens")
a = ap.parse_args()

now = lambda: datetime.now(timezone.utc)
run_start = now()
os.makedirs(a.out, exist_ok=True)
raw_path = os.path.join(a.out, f"raw-{run_start.astimezone(SYDNEY).strftime('%Y-%m-%dT%H%M')}.jsonl.gz")
raw = gzip.open(raw_path, "at", encoding="utf-8")
raw_lock = threading.Lock()


def log(kind, **kw):
    with raw_lock:
        raw.write(json.dumps({"_at": now().isoformat(timespec="seconds"), "_kind": kind, **kw}) + "\n")


bm = BM()
token = bm.h["Authorization"].split(" ", 1)[1]
ready = bm.get("/account/readiness/")
bots = ready.get("bot_session_running") if isinstance(ready, dict) else None
print(f"BetMatic readiness: bot machines connected {bots}; problems {ready.get('problems') if isinstance(ready, dict) else ready}")
if not bots:
    print("WARNING: no bot machine connected. BetMatic only answers odds requests from a running bot; this run will "
          "record nothing until it connects.")

answers: "queue.Queue[tuple[datetime, dict]]" = queue.Queue()


def on_message(ws, message):
    t = now()
    try:
        m = json.loads(message)
    except ValueError:
        log("unparsed", raw=message[:2000]); return
    if m.get("category") == "odds_update_anwser":   # spelt that way by the API
        answers.put((t, m))
    else:
        log("message", category=m.get("category"), message=m)


ws = websocket.WebSocketApp(f"wss://betmatic.app/ws/private?token={token}", on_message=on_message,
                            on_open=lambda w: print("websocket connected"),
                            on_error=lambda w, e: print("websocket error:", e),
                            on_close=lambda w, c, msg: print("websocket closed:", c, msg))
threading.Thread(target=lambda: ws.run_forever(reconnect=5), daemon=True).start()
time.sleep(5)

books: dict[str, RaceBook] = {}
stats = Counter()
end = run_start + timedelta(hours=a.hours)
next_schedule = run_start
next_write = run_start + timedelta(minutes=10)
every, open_every = timedelta(seconds=a.every), timedelta(seconds=a.open_every)
sample_shown = False


def drain(tag):
    """Answers nobody is waiting for: logged, never filed."""
    while True:
        try:
            t, m = answers.get_nowait()
        except queue.Empty:
            return
        stats["unattributed"] += 1
        log("unattributed", why=tag, received=t.isoformat(timespec="seconds"), message=m)


def write_csvs():
    by_day: dict[str, list[dict]] = {}
    for rb in books.values():
        for r in rb.rows():
            by_day.setdefault(r["date"], []).append(r)
    for day, rows in by_day.items():
        path = os.path.join(a.out, f"opens-{day}.csv.gz")
        old = []
        if os.path.exists(path):
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                old = list(csv.DictReader(fh))
        merged = merge_rows(old, [{k: str(v) for k, v in r.items()} for r in rows])
        tmp = path + ".part"
        with gzip.open(tmp, "wt", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=ROW_FIELDS); w.writeheader(); w.writerows(merged)
        os.replace(tmp, path)


try:
    while now() < end:
        if now() >= next_schedule:
            rows = bm.get_all("/competition/namecodes/")
            races = select_races(rows, now(), a.state, timedelta(hours=a.ahead))
            for r in races:
                rb = books.setdefault(r.key, RaceBook(r))
                rb.race = r          # a start time BetMatic has moved since the last read
            if not sample_shown:
                g = sorted({str(x.get("name")) for x in rows if isinstance(x, dict) and x.get("code") == "Greyhounds"})
                print(f"schedule: {len(rows)} rows, {len(g)} greyhound venues: {', '.join(g)}")
                if races:
                    print(f"startTime sample: raw {races[0].start_raw!r} read as {races[0].start.astimezone(SYDNEY).isoformat()}"
                          " (Sydney). Check this against the race's real start before trusting the windows.")
                sample_shown = True
            print(f"{now().astimezone(SYDNEY):%H:%M} {len(races)} {a.state} greyhound races to watch")
            next_schedule = now() + timedelta(minutes=15)
        due = [rb for rb in books.values() if rb.due(now(), every, open_every)]
        if not due:
            if now() >= next_write:
                write_csvs(); next_write = now() + timedelta(minutes=10)
            time.sleep(5); continue
        for rb in sorted(due, key=lambda x: x.race.start):
            if now() >= end:
                break
            drain("before request")
            body = {"code": "Greyhounds", "competition": rb.race.venue, "event_number": rb.race.number}
            sent = now(); rb.note_poll(sent); stats["requests"] += 1
            code, resp = bm.post("/notification/odds/request/", body)
            log("request", race=rb.race.key, status=code, response=str(resp)[:300])
            if code != 200:
                stats[f"request {code}"] += 1; continue
            try:
                t, m = answers.get(timeout=a.wait)
            except queue.Empty:
                stats["no answer"] += 1; log("no_answer", race=rb.race.key); continue
            rb.record(t, m.get("data")); stats["answered"] += 1
            log("answer", race=rb.race.key, received=t.isoformat(timespec="seconds"), data=m.get("data"))
            time.sleep(0.5); drain(f"extra after {rb.race.key}")
        if now() >= next_write:
            write_csvs(); next_write = now() + timedelta(minutes=10)
finally:
    write_csvs()
    ws.close(); raw.close()

print("\n## Greyhound opens: this run")
print(f"{dict(stats)}")
opened = [rb for rb in books.values() if rb.tab_open]
known = [rb for rb in opened if rb.books["TAB"].open_known]
print(f"races watched {len(books)}; TAB priced {len(opened)}; TAB open window caught {len(known)}")
for rb in sorted(known, key=lambda x: x.race.start)[:40]:
    b = rb.books["TAB"]
    before = (rb.race.start - b.first_seen).total_seconds() / 3600
    print(f"- {rb.race.venue} R{rb.race.number}: TAB opened between {b.last_closed.astimezone(SYDNEY):%H:%M} and "
          f"{b.first_seen.astimezone(SYDNEY):%H:%M}, {before:.1f}h before the jump")
first = Counter()
for rb in opened:
    seen = [(bo.first_seen, name) for name, bo in rb.books.items() if bo.first_seen and bo.open_known]
    if seen:
        first[min(seen)[1]] += 1
print(f"first bookmaker to open (races where the window was caught): {dict(first)}")
if not stats.get("answered"):
    print("NO answers: the bot must be running with its TAB session online for BetMatic to answer odds requests")
print(f"files: {a.out}/opens-<day>.csv.gz, raw log {raw_path}")
