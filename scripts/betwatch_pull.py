"""TAB's fixed win prices for every Victorian thoroughbred runner, from Betwatch's current API (13 Nov 2026; founder's
trial key to 20 Nov). For the 9am rule's backtest: Form King's stored flucs miss Nov 2025 - Aug 2026, Betwatch holds
TAB's flucs with timestamps back to Nov 2022 (Jamie Watts, Betwatch, 13 Nov: "Each bookie's flucs come through with
timestamps up to the jump, TAB included. The first price we have ... is usually close to the open but can miss sharp
early moves").

    python scripts/betwatch_pull.py DATE_FROM DATE_TO

One row per runner, between CSV-BEGIN and CSV-END: date, track, race, number, name, scratched, tab_first, tab_first_mel,
tab_0900 (TAB's last price at or before 9:00am Melbourne on race day, blank if none yet), tab_0900_mel, tab_last,
tab_last_mel, flucs (count), jump_mel (the race's actual start, else its scheduled start), path (EVERY TAB price
move from the first: "minutes after tab_first_mel:price;..." to two decimals of a minute, so any time from the open to
the jump can be read off: 13 Nov 2026, founder: "we can more properly do all the times up to race start? From odds
opening?"). Key from BETWATCH_API_KEY, never printed. Used for our own model only, not shared or resold
(Betwatch's terms, confirmed by email 13 Nov)."""
import csv, datetime as dt, os, subprocess, sys, time
from zoneinfo import ZoneInfo

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "betwatch", "backoff", "gql[all]", "pydantic"], check=False)
import betwatch
from betwatch.types import RaceProjection, RacesFilter

KEY = os.environ["BETWATCH_API_KEY"].strip()
MEL, UTC = ZoneInfo("Australia/Melbourne"), dt.timezone.utc
d0, d1 = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2])
client = betwatch.connect(api_key=KEY)
proj = RaceProjection(markets=True, flucs=True, bookmakers=["Tab"])


def ts(x):
    if x is None: return None
    if isinstance(x, dt.datetime): return x if x.tzinfo else x.replace(tzinfo=UTC)
    return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00"))


def g(o, *names):
    for n in names:
        v = getattr(o, n, None) if not isinstance(o, dict) else o.get(n)
        if v is not None: return v
    return None


w = csv.writer(sys.stdout)
print("CSV-BEGIN")
w.writerow(["date", "track", "race", "number", "name", "scratched", "tab_first", "tab_first_mel", "tab_0900", "tab_0900_mel",
            "tab_last", "tab_last_mel", "flucs", "jump_mel", "path"])
days, races_n, rows_n, fails = 0, 0, 0, []
d = d0
while d <= d1:
    nine = dt.datetime.combine(d, dt.time(9, 0), tzinfo=MEL).astimezone(UTC)
    got = None
    for attempt in range(4):
        try:
            got = client.get_races_between_dates(str(d), str(d), projection=proj,
                                                 filter=RacesFilter(locations=["VIC"], types=["Thoroughbred"], limit=100))
            break
        except Exception as ex:
            time.sleep(10 * (attempt + 1))
            if attempt == 3: fails.append(f"{d}: {type(ex).__name__} {str(ex).replace(KEY, '<KEY>')[:150]}")
    for r in got or []:
        races_n += 1
        meet = g(r, "meeting"); track = g(meet, "track") or ""; num = g(r, "number")
        jump = ts(g(r, "actual_start_time", "_actual_start_time") or g(r, "start_time", "_start_time"))
        for ru in g(r, "runners") or []:
            fl, last = [], None
            for bm in g(ru, "bookmaker_markets") or []:
                if str(g(bm, "_bookmaker", "bookmaker") or "").lower() != "tab": continue
                fw = g(bm, "_fixed_win", "fixed_win")
                if not fw: continue
                fl = sorted(((ts(g(f, "_last_updated", "last_updated")), g(f, "price")) for f in (g(fw, "flucs") or [])
                             if g(f, "price")), key=lambda x: x[0])
                last = (ts(g(fw, "_last_updated", "last_updated")), g(fw, "price"))
            first = fl[0] if fl else None
            at9 = next((f for f in reversed(fl) if f[0] <= nine), None)
            if last is None and fl: last = fl[-1]
            m = lambda x: x.astimezone(MEL).strftime("%Y-%m-%d %H:%M") if x else ""
            w.writerow([d, track, num, g(ru, "number"), g(ru, "name"), 1 if g(ru, "scratched_time", "_scratched_time") else 0,
                        first[1] if first else "", m(first[0]) if first else "", at9[1] if at9 else "", m(at9[0]) if at9 else "",
                        last[1] if last else "", m(last[0]) if last and last[0] else "", len(fl), m(jump) if jump else "",
                        ";".join(f"{(t - first[0]).total_seconds() / 60:.2f}:{pr:g}" for t, pr in fl) if first else ""])
            rows_n += 1
    days += 1
    d += dt.timedelta(days=1)
    time.sleep(0.5)
print("CSV-END")
print(f"{days} days, {races_n} VIC thoroughbred races, {rows_n} runners; failed days: {len(fails)}")
for f in fails: print("FAILED", f)
