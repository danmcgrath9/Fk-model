"""Every bookmaker's price, race by race, from our own BetMatic bot (18 Oct 2026, founder: see which bookmakers open
after TAB, how quickly, and how far off TAB's opening price they are). Needs WebSocket access (enabled 18 Oct) and the
bot running with its sessions online: the odds are read by OUR bot from OUR logged-in accounts, so only bookmakers we
hold a running session with appear.

    python betmatic/odds_watch_live.py --venue KYNETON --date 2026-10-20 [--every 60] [--minutes 240] [--races 1,2,3]
           [--out data/live_bets/odds-live-2026-10-20-kyneton.jsonl]

Every --every seconds, POST /notification/odds/request/ for each race; every WebSocket message is appended raw to the
log with the time received. The odds payload's fields are not documented, so the log is raw and the summary at the end
is generic (messages per race, first and last answer, the keys seen); a proper per-bookmaker table is written from the
first real log."""
import argparse, json, os, sys, threading, time, collections
import websocket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from betmatic_send import BM, API

ap = argparse.ArgumentParser()
ap.add_argument("--venue", required=True); ap.add_argument("--date", required=True)
ap.add_argument("--every", type=int, default=60); ap.add_argument("--minutes", type=int, default=240)
ap.add_argument("--races", default=""); ap.add_argument("--out", default="")
a = ap.parse_args()
venue = a.venue.upper(); out = a.out or f"data/live_bets/odds-live-{a.date}-{a.venue.lower()}.jsonl"
bm = BM(); token = bm.h["Authorization"].split(" ", 1)[1]

sched = [c for c in bm.get_all("/competition/namecodes/") if isinstance(c, dict) and c.get("code") == "Galloping"
         and str(c.get("name", "")).upper() == venue and str(c.get("startTime", ""))[:10] == a.date]
races = sorted({int(c["event_number"]) for c in sched})
if a.races:
    races = [r for r in races if r in {int(x) for x in a.races.split(",")}]
if not races:
    sys.exit(f"{venue} on {a.date} is not in BetMatic's race schedule (names are the exact uppercase venue names)")
print(f"{venue} {a.date}: races {races}; a request every {a.every}s for {a.minutes} min; logging to {out}")
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
stats = collections.Counter(); keys = collections.Counter(); first_last = {}
lock = threading.Lock()

def on_message(ws, message):
    t = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    try: m = json.loads(message)
    except ValueError: m = {"category": "unparsed", "raw": message}
    m["_received"] = t
    with lock:
        with open(out, "a") as fh: fh.write(json.dumps(m) + "\n")
        cat = m.get("category"); stats[cat] += 1
        d = m.get("data")
        if isinstance(d, dict): keys.update(d.keys())
        elif isinstance(d, list) and d and isinstance(d[0], dict): keys.update(d[0].keys())
        first_last.setdefault(cat, [t, t])[1] = t

ws = websocket.WebSocketApp(f"wss://betmatic.app/ws/private?token={token}", on_message=on_message,
                            on_open=lambda w: print("websocket connected"),
                            on_error=lambda w, e: print("websocket error:", e),
                            on_close=lambda w, c, msg: print("websocket closed:", c, msg))
threading.Thread(target=lambda: ws.run_forever(reconnect=5), daemon=True).start()
time.sleep(5)
end = time.time() + a.minutes * 60; n = 0
while time.time() < end:
    n += 1
    for r in races:
        code, body = bm.post("/notification/odds/request/", {"code": "Galloping", "competition": venue, "event_number": r})
        if code != 200: print(f"request R{r}: {code} {str(body)[:120]}")
        time.sleep(1)
    print(f"round {n} sent at {time.strftime('%H:%M:%S')}; messages so far {dict(stats)}")
    time.sleep(max(0, a.every - len(races)))
time.sleep(30); ws.close()
print("\n## Summary")
print(f"requests: {n} rounds x {len(races)} races; messages by category: {dict(stats)}")
for cat, (f, l) in first_last.items(): print(f"- {cat}: first {f}, last {l}")
print(f"keys seen in data: {dict(keys)}")
if not stats.get("odds_update_anwser"):
    print("NO odds answers: the bot must be running with its sessions online for BetMatic to answer odds requests")
