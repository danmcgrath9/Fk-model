"""Record TAB's opening price for every Australian harness runner, with the time it was first seen (25 Oct 2026).

The harness brief's hard requirement is a TIMESTAMPED OPENING PRICE per runner. No historical source holds one (the
Phase 1 search: PuntersEdge only from 4 Aug 2026, nothing free), so this records it forward from our own BetMatic bot.
READ-ONLY: it sends odds requests only, never a bet.

    python betmatic/harness_open_watch.py [--minutes 330] [--every 120] [--far-every 600] [--far-hours 6]
                                          [--horizon 36] [--out data/harness_opens]

It asks BetMatic for TAB's prices on each Australian harness race (config/harness_au_tracks.txt) in BetMatic's schedule
that starts within --horizon hours and has not jumped: every --far-every seconds while the race is more than
--far-hours away, every --every seconds after that, one request at a time, waiting for that race's answer before the
next (the answer carries no race id; it is paired with the request echo that precedes it on the WebSocket). An empty answer means the
market is not up yet. The first answer with a price opens the race.

What is stored, one JSON file per race date (data/harness_opens/YYYY-MM-DD.json), per race:
- last_empty_at: the last poll that found no market; opened_at: the first poll that found prices. The market opened
  between the two, so the gap is the honest error on the open's timestamp.
- open_seen_on_first_poll: true when the very first poll already found prices. Then opened_at is only when WE first
  looked, not when TAB opened, and those prices may already have moved: leave such races out of any open-price test.
- per runner, per bookmaker: the first win and place price seen and when. A runner priced after the race opened has its
  own first_seen_at. A scratched runner is marked, with the time it was first seen scratched.
Polling a race stops once every runner in the schedule has a price or is scratched, or once the race has started.

Needs the bot running with its TAB session online at the times markets open (BetMatic answers odds requests from OUR
bot's logged-in sessions; no bot = no answer). The script stops at the start if BetMatic reports no bot connected."""
import argparse, datetime as dt, json, os, queue, sys, threading, time

UTC = dt.timezone.utc
CODE = "Harness"


def now_utc():
    return dt.datetime.now(UTC)


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_start(s):
    """BetMatic's startTime as an aware datetime. A value we cannot read stops the run with the value named, rather than
    being guessed at: polling the wrong window would record the wrong open."""
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"cannot read BetMatic startTime {s!r}: fix parse_start before recording")
    if t.tzinfo is None:
        raise SystemExit(f"BetMatic startTime {s!r} has no timezone: fix parse_start before recording")
    return t


def race_key(venue, number):
    return f"{venue}|R{int(number)}"


TRACKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "harness_au_tracks.txt")


def australian_tracks(path=TRACKS):
    """The Australian harness venues to watch (BetMatic's schedule also carries France, North America and NZ)."""
    return {l.strip().upper() for l in open(path) if l.strip() and not l.startswith("#")}


def schedule_races(sched, now, horizon_hours, allowed=None, skipped=None):
    """Harness races from GET /competition/namecodes/ that start after now and within the horizon, at an allowed
    venue when a set is given. Venues left out are added to `skipped`, so a misspelt Australian track shows up."""
    out = []
    for c in sched:
        if not isinstance(c, dict) or c.get("code") != CODE:
            continue
        venue = str(c.get("name", "")).upper()
        if allowed is not None and venue not in allowed:
            if skipped is not None:
                skipped.add(venue)
            continue
        start = parse_start(c.get("startTime"))
        if now < start <= now + dt.timedelta(hours=horizon_hours):
            out.append({"venue": str(c.get("name", "")).upper(), "race": int(c.get("event_number", 0)),
                        "start_time": str(c.get("startTime")), "date": str(c.get("startTime"))[:10],
                        "runners": [x.strip() for x in str(c.get("runners", "")).split(",") if x.strip()]})
    return out


def poll_interval(start, now, every, far_every, far_hours):
    """Seconds between asks for one race: every `far_every` while the start is more than `far_hours` away, every
    `every` after that. Lighter polling for far-off races keeps the reads through our TAB and Sportsbet sessions down
    (about a quarter of the first run's), at the price of a wider bracket on an open that lands far from the jump."""
    return far_every if start - now > dt.timedelta(hours=far_hours) else every


def new_race(r):
    return {"venue": r["venue"], "race": r["race"], "start_time": r["start_time"], "field": r["runners"],
            "field_at_first_look": list(r["runners"]),
            "polls": 0, "first_poll_at": None, "last_empty_at": None, "opened_at": None,
            "open_seen_on_first_poll": None, "runners": {}}


def record(race, answer, at):
    """Fold one odds answer (a list of {number, bookie_odds: [{name, win, place, scratched}]}) into a race's record.
    Only the FIRST price per runner per bookmaker is kept; later answers can only add runners or bookmakers not yet
    seen. Returns True when this answer opened the race."""
    t = iso(at)
    first = race["polls"] == 0
    race["polls"] += 1
    if race["first_poll_at"] is None:
        race["first_poll_at"] = t
    priced = False
    for r in answer or []:
        num = str(r.get("number"))
        for b in r.get("bookie_odds") or []:
            name = str(b.get("name"))
            if b.get("scratched"):
                race["runners"].setdefault(num, {}).setdefault(name, {"scratched": True, "first_seen_at": t})
                continue
            win = float(b.get("win") or 0)
            if win <= 0:
                continue
            priced = True
            slot = race["runners"].setdefault(num, {})
            if name not in slot or slot[name].get("scratched"):
                slot[name] = {"win": win, "place": float(b.get("place") or 0) or None, "first_seen_at": t}
    if race["opened_at"] is None:
        if priced:
            race["opened_at"] = t
            race["open_seen_on_first_poll"] = first
            return True
        race["last_empty_at"] = t
    return False


def complete(race, bookie="TAB"):
    """Every runner in the scheduled field has a first price or is scratched at this bookmaker."""
    if race["opened_at"] is None or not race["field"]:
        return False
    return all(bookie in race["runners"].get(n, {}) for n in race["field"])


class Answers:
    """Pairs each odds answer with the request echo before it. BetMatic's answer has no race id: the WebSocket sends
    our request back (category request_odds) and then the answer (odds_update_anwser, spelt as sent)."""

    def __init__(self):
        self.q = queue.Queue(); self.current = None

    def on_message(self, message):
        try:
            m = json.loads(message)
        except ValueError:
            return
        d = m.get("data")
        if m.get("category") == "request_odds" and isinstance(d, dict):
            self.current = (str(d.get("competition", "")).upper(), int(d.get("event_number") or 0), d.get("code"))
        elif m.get("category") == "odds_update_anwser":
            self.q.put((self.current, d, now_utc()))

    def wait_for(self, venue, race, timeout):
        """The answer for this race, or None. Answers for anything else (late ones from an earlier request) are
        discarded, so a slow answer can never be filed under the wrong race."""
        end = time.time() + timeout
        while time.time() < end:
            try:
                key, data, at = self.q.get(timeout=max(0.1, end - time.time()))
            except queue.Empty:
                return None
            if key == (venue, race, CODE):
                return data, at
        return None


def load(path):
    return json.load(open(path)) if os.path.exists(path) else {}


def save(path, day):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(day, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def main():
    import websocket
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from betmatic_send import BM

    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=330); ap.add_argument("--every", type=int, default=120)
    ap.add_argument("--far-every", type=int, default=600); ap.add_argument("--far-hours", type=float, default=6)
    ap.add_argument("--horizon", type=float, default=36); ap.add_argument("--wait", type=int, default=20)
    ap.add_argument("--out", default="data/harness_opens")
    a = ap.parse_args()

    bm = BM(); token = bm.h["Authorization"].split(" ", 1)[1]
    ready = bm.get("/account/readiness/")
    if not (ready or {}).get("bot_session_running"):
        sys.exit(f"BetMatic reports no bot machine connected ({ready}): odds requests would go unanswered. Not recording.")

    ans = Answers()
    ws = websocket.WebSocketApp(f"wss://betmatic.app/ws/private?token={token}",
                                on_message=lambda w, m: ans.on_message(m),
                                on_open=lambda w: print("websocket connected"),
                                on_error=lambda w, e: print("websocket error:", e),
                                on_close=lambda w, c, msg: print("websocket closed:", c, msg))
    threading.Thread(target=lambda: ws.run_forever(reconnect=5), daemon=True).start()
    time.sleep(5)

    end = time.time() + a.minutes * 60
    days, sched_at, races, n_pass = {}, 0.0, [], 0
    unanswered, asked, last_ask = 0, 0, {}
    while time.time() < end:
        t0 = time.time(); n_pass += 1
        if t0 - sched_at > 1800:                      # new meetings join the schedule during the day
            sched = bm.get_all("/competition/namecodes/")
            codes = sorted({str(c.get("code")) for c in sched if isinstance(c, dict)})
            if CODE not in codes:
                sys.exit(f"no {CODE!r} races in BetMatic's schedule (codes seen: {codes}). Not recording.")
            skipped = set()
            races = schedule_races(sched, now_utc(), a.horizon, australian_tracks(), skipped); sched_at = t0
            print(f"schedule: {len(races)} Australian harness races within {a.horizon}h; "
                  f"venues skipped (not in config/harness_au_tracks.txt): {', '.join(sorted(skipped)) or 'none'}")
        opened = 0
        for r in races:
            if time.time() >= end:
                break
            path = os.path.join(a.out, f"{r['date']}.json")
            day = days.setdefault(path, load(path))
            rec = day.setdefault(race_key(r["venue"], r["race"]), new_race(r))
            rec["field"] = r["runners"]; rec["start_time"] = r["start_time"]   # scratched runners leave the schedule
            start, now = parse_start(r["start_time"]), now_utc()
            if now >= start or complete(rec):
                continue
            key = race_key(r["venue"], r["race"])
            if time.time() - last_ask.get(key, 0) < poll_interval(start, now, a.every, a.far_every, a.far_hours):
                continue
            last_ask[key] = time.time(); asked += 1
            code, body = bm.post("/notification/odds/request/", {"code": CODE, "competition": r["venue"],
                                                                 "event_number": r["race"]})
            if code != 200:
                print(f"{r['venue']} R{r['race']}: request {code} {str(body)[:120]}"); continue
            got = ans.wait_for(r["venue"], r["race"], a.wait)
            if got is None:
                unanswered += 1; print(f"{r['venue']} R{r['race']}: no answer in {a.wait}s"); continue
            if record(rec, got[0], got[1]):
                opened += 1
                print(f"OPEN {r['venue']} R{r['race']} at {rec['opened_at']} (last empty {rec['last_empty_at']})")
            save(path, day)
        if opened or n_pass % 30 == 0:
            print(f"pass {n_pass} at {iso(now_utc())}: {opened} opened; {asked} asked, {unanswered} unanswered so far")
        time.sleep(max(0, 15 - (time.time() - t0)))      # a short tick: each race is asked only when it is due
    ws.close()
    print(f"asked {asked} times in {a.minutes} min; {unanswered} unanswered")
    for path, day in days.items():
        save(path, day)
        op = [v for v in day.values() if v["opened_at"]]
        print(f"{path}: {len(day)} races watched, {len(op)} open, "
              f"{sum(1 for v in op if v['open_seen_on_first_poll'])} already open at our first look")


if __name__ == "__main__":
    main()
