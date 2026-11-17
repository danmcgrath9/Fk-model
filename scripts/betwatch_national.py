"""Every state's thoroughbred races from Betwatch, slim (18 Nov 2026; founder's trial key to 20 Nov; founder, 18 Nov: "You
have unlimited research time ... get us sharper"). For the tests that need NO model, so they can be run on five times
the races: the 9am rule on the market alone (research/form_gbm/night r9/b_nomodel.py: the majors' median price, the
move since the open) and every rule that reads only the open and Betfair SP.

    python scripts/betwatch_national.py DATE_FROM DATE_TO [STATE,STATE,...]

One row per runner between CSV-BEGIN and CSV-END. Times are minutes relative to the jump (negative = before).
  date, state, track, race, number, name, barrier, emergency
  scr_min     when it was scratched (blank = ran)          nine_min   9:00am local time on race day
  jump_utc, status, pos (1-4 from the race's results, 0 = unplaced, blank = no result), dist, cls, cond
  bsp, bf_matched (Betfair win market: this runner, $), bf_mkt (the whole market, $)
  for each major (tab sportsbet ladbrokes neds pointsbet unibet betr):
      <bk>_first:<minute>   first price and when     <bk>_0900  last price at or before 9:00am local
      <bk>_t240 _t60 _t10 _t1   last price at or before 240 / 60 / 10 / 1 minutes before the jump   <bk>_n  moves
  x9: the 9:00am price of seven smaller bookmakers ("bookie:price;...")     last_min: the last price move of any of them
Key from BETWATCH_API_KEY, never printed. Our own use only, not shared or resold (Betwatch's terms, 13 Nov)."""
import csv, datetime as dt, os, subprocess, sys, time
from zoneinfo import ZoneInfo

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "betwatch", "backoff", "gql[all]", "pydantic"], check=False)
import betwatch
from betwatch.types import RaceProjection, RacesFilter

KEY = os.environ["BETWATCH_API_KEY"].strip()
UTC = dt.timezone.utc
TZ = {"VIC": "Australia/Melbourne", "NSW": "Australia/Sydney", "ACT": "Australia/Sydney", "TAS": "Australia/Hobart",
      "QLD": "Australia/Brisbane", "SA": "Australia/Adelaide", "NT": "Australia/Darwin", "WA": "Australia/Perth"}
MAJORS = ["tab", "sportsbet", "ladbrokes", "neds", "pointsbet", "unibet", "betr"]
EXTRA = ["tabtouch", "dabble", "palmerbet", "swiftbet", "betright", "picnicbet", "betdeluxe"]
d0, d1 = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2])
STATES = sys.argv[3].split(",") if len(sys.argv) > 3 else ["NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT", "VIC"]
client = betwatch.connect(api_key=KEY)
proj = RaceProjection(markets=True, flucs=True, betfair=True, bookmakers=[b.capitalize() for b in MAJORS + EXTRA])


def ts(x):
    if not x: return None
    t = dt.datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def at(fl, t):
    """Last price at or before t."""
    p = None
    for a, pr in fl:
        if a <= t: p = pr
        else: break
    return p


w = csv.writer(sys.stdout)
print("CSV-BEGIN")
head = ["date", "state", "track", "race", "number", "name", "barrier", "emergency", "scr_min", "nine_min", "jump_utc", "status", "pos",
        "dist", "cls", "cond", "bsp", "bf_matched", "bf_mkt"]
for b in MAJORS: head += [f"{b}_first", f"{b}_0900", f"{b}_t240", f"{b}_t60", f"{b}_t10", f"{b}_t1", f"{b}_n"]
w.writerow(head + ["x9", "last_min"])
days, races_n, rows_n, fails, t_start = 0, 0, 0, [], time.time()
d = d0
while d <= d1:
    for st in STATES:
        nine = dt.datetime.combine(d, dt.time(9, 0), tzinfo=ZoneInfo(TZ[st])).astimezone(UTC)
        got, off = [], 0
        while True:
            page = None
            for attempt in range(4):
                try:
                    page = client.get_races_between_dates(str(d), str(d), projection=proj, parse_result=False,
                                                          filter=RacesFilter(locations=[st], types=["Thoroughbred"], limit=100, offset=off))
                    break
                except Exception as ex:
                    time.sleep(10 * (attempt + 1))
                    if attempt == 3: fails.append(f"{d} {st}: {type(ex).__name__} {str(ex).replace(KEY, '<KEY>')[:120]}")
            got += page or []
            if not page or len(page) < 100: break
            off += 100
        for r in got:
            races_n += 1
            meet = r.get("meeting") or {}
            jump = ts(r.get("actualStartTime") or r.get("startTime"))
            if jump is None: continue
            res = r.get("results") or []
            pos = {}
            for k, grp in enumerate(res[:4]):
                for num in (grp if isinstance(grp, list) else [grp]): pos[str(num)] = k + 1
            mn = lambda t: f"{(t - jump).total_seconds() / 60:.1f}" if t else ""
            for ru in r.get("runners") or []:
                book, last = {}, None
                for bm in ru.get("bookmakerMarkets") or []:
                    bk = str(bm.get("bookmaker") or "").lower(); fw = bm.get("fixedWin")
                    if not fw: continue
                    fl = sorted(((ts(f.get("lastUpdated")), f.get("price")) for f in (fw.get("flucs") or []) if f.get("price") and f["price"] > 1 and f.get("lastUpdated")),
                                key=lambda x: x[0])
                    if fl:
                        book[bk] = fl
                        if last is None or fl[-1][0] > last: last = fl[-1][0]
                bf = next((m for m in (ru.get("betfairMarkets") or []) if "place" not in str(m.get("marketName") or "").lower()), None) or {}
                row = [d, st, meet.get("track") or "", r.get("number"), ru.get("number"), ru.get("name"), ru.get("barrier") or "",
                       1 if ru.get("emergency") else 0, mn(ts(ru.get("scratchedTime"))), mn(nine), jump.strftime("%Y-%m-%dT%H:%M"),
                       r.get("status") or "", (pos.get(str(ru.get("number")), 0) if res else ""), r.get("distance") or "",
                       str(r.get("classConditions") or "")[:40], str(r.get("trackCondition") or "")[:12],
                       bf.get("sp") or "", f"{bf.get('totalMatched') or 0:.0f}", f"{bf.get('marketTotalMatched') or 0:.0f}"]
                for b in MAJORS:
                    fl = book.get(b)
                    if not fl: row += [""] * 7; continue
                    g = lambda m_: at(fl, jump - dt.timedelta(minutes=m_)) or ""
                    row += [f"{fl[0][1]:g}:{mn(fl[0][0])}", at(fl, nine) or "", g(240), g(60), g(10), g(1), len(fl)]
                row += [";".join(f"{b}:{at(book[b], nine):g}" for b in EXTRA if b in book and at(book[b], nine)), mn(last)]
                w.writerow(row); rows_n += 1
        time.sleep(0.3)
    days += 1
    d += dt.timedelta(days=1)
print("CSV-END")
print(f"{days} days, {races_n} races, {rows_n} runners, states {','.join(STATES)}, {time.time() - t_start:.0f}s; failed: {len(fails)}")
for f in fails[:30]: print("FAILED", f)
