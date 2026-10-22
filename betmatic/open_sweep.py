"""After a meeting opens: which of our runners have nothing on, and is TAB's live price still at or above the order's
minimum? Writes the steps that would fill now as a "place now" order file, for the founder's OK (21 Oct 2026: open
orders that did not fire left value on the table at Mornington, Flemington and Cranbourne; finding it by hand took a
dozen steps). Read-only: nothing is sent here; the file goes through fk-betmatic (send, when now, a tag) after his OK.

    python betmatic/open_sweep.py data/live_bets/2026-10-23-ballarat-betmatic-preopen.csv

Reads TAB's latest win price per runner from the meeting's odds log (odds_watch_live.py), and every bet record of the
meeting from its *-placed.jsonl files (fk-betmatic status). A runner with ANY money on (any file, any step) is left
out, so a sweep can never double a bet; a part-filled ladder (eg one of two steps) is listed as on, and named."""
import csv, glob, json, os, sys, collections

orders = sys.argv[1]
base = os.path.basename(orders).split("-betmatic-")[0]            # 2026-10-23-ballarat
date, venue = base[:10], base[11:]
L = os.path.dirname(orders) or "."
out = os.path.join(L, f"{base}-sweep.csv")

odds, when = {}, None
log = os.path.join(L, f"odds-live-{date}-{venue}.jsonl")
if os.path.exists(log):
    cur = None
    for line in open(log):
        d = json.loads(line)
        if d.get("category") == "request_odds":
            cur = d["data"].get("event_number")
        elif d.get("category") == "odds_update_anwser" and cur is not None:
            for r in d.get("data") or []:
                for b in r.get("bookie_odds", []):
                    if b.get("name") == "TAB" and b.get("win") and not b.get("scratched"):
                        odds[(int(cur), str(r["number"]))] = float(b["win"]); when = d.get("_received")
if not odds:
    sys.exit(f"no TAB prices in {log}: the market is not up on BetMatic yet (run the odds watch first)")

took = collections.defaultdict(float); part = set()
for f in glob.glob(os.path.join(L, f"{base}*-placed.jsonl")):
    for line in open(f):
        d = json.loads(line)
        lab = d["label"]                                           # fk-2026-10-23-ballarat-r2-n6-s1[-tag]
        rn = lab.split(f"-{venue}-r", 1)[1].split("-")
        for x in d.get("records") or []:
            if isinstance(x, dict) and float(x.get("amount") or 0) > 0:
                took[(int(rn[0]), rn[1][1:])] = took[(int(rn[0]), rn[1][1:])] + float(x["amount"])

rows = list(csv.DictReader(open(orders)))
by = collections.OrderedDict()
for r in rows:
    by.setdefault((int(r["race"]), str(r["number"]), r["horse"]), []).append(r)
keep, lines = [], []
for (rc, n, h), rs in sorted(by.items(), key=lambda x: (x[0][0], int(x[0][1] or 0))):
    w = odds.get((rc, n)); mn = min(float(r["min_odds"]) for r in rs)
    if took[(rc, n)] > 0:
        lines.append(f"R{rc} {h:20s} on already (${took[(rc, n)]:.0f})"); continue
    if w is None:
        lines.append(f"R{rc} {h:20s} no TAB price"); continue
    fill = [r for r in rs if float(r["min_odds"]) <= w <= float(r["max_odds"])]
    if fill:
        keep += fill
        lines.append(f"R{rc} {h:20s} TAB ${w:.2f} >= min ${mn:.2f}: {sum(float(r['stake_units']) for r in fill):.2f}u  <- SWEEP")
    else:
        lines.append(f"R{rc} {h:20s} TAB ${w:.2f}, min ${mn:.2f}: no")
print(f"{base}: TAB prices as at {when}")
print("\n".join(lines))
with open(out, "w", newline="") as fh:
    wtr = csv.DictWriter(fh, fieldnames=rows[0].keys()); wtr.writeheader(); wtr.writerows(keep)
print(f"{len(keep)} steps on {len({(r['race'], r['number']) for r in keep})} runners to place now -> {out}"
      + ("" if keep else " (nothing to do)"))
