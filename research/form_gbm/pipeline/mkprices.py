"""A live_bets prices file from scratchings.py output, on the FINAL field.
    python3.13 mkprices.py SCR_OUTPUT.md ENTRY_NUMBERS.txt OUT.txt "# header line" [--race-morning | --not-race-morning]

SCR_OUTPUT.md is the fk-experiment output of scripts/scratchings.py (its "## prices file" section is the body);
ENTRY_NUMBERS.txt is entry_numbers.py output (race|number|name|emergency|scratched).

Emergencies (14 Oct 2026, betmatic_orders.py "FINAL FIELD ONLY"): an emergency is priced as SCR, because pricing it in
spreads the race's probability over a horse that will not run. On race morning Form King scratches the emergencies
that did not gain a start, so an emergency still standing on race morning has gained one and is priced in. Race morning
is the meeting's own date in Melbourne (from the section's meeting id), unless a flag says otherwise. Every runner the
entry numbers scratch is SCR too, even when the prices section was fetched before the scratching.
Prints: "<file> priced N SCR M emergencies in: [...]"."""
import datetime as dt
import re
import sys
from zoneinfo import ZoneInfo

scr_fn, nums_fn, out, head = sys.argv[1:5]
flags = sys.argv[5:]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

txt = open(scr_fn).read()
m = re.search(r"## prices file: (\S+)\n(.*?)(?:\n\s*\n|\Z)", txt, re.S)
if not m:
    sys.exit(f"STOP: no '## prices file' section in {scr_fn}")
mid, body = m.group(1), [l for l in m.group(2).split("\n") if l.strip() and l[0].isdigit()]
md = re.search(r"(\d{8})$", mid)
today = dt.datetime.now(ZoneInfo("Australia/Melbourne")).strftime("%Y%m%d")
race_morning = ("--race-morning" in flags) or (md is not None and md.group(1) == today and "--not-race-morning" not in flags)

status = {}
for l in open(nums_fn):
    pa = l.strip().split("|")
    if len(pa) == 5 and pa[0].isdigit():
        status[(int(pa[0]), norm(pa[2]))] = (pa[3] == "True", pa[4] == "True")
if not status:
    sys.exit(f"STOP: {nums_fn} has no race|number|name|emergency|scratched lines")

res, n_in, n_scr, em_in, unknown = [head], 0, 0, [], []
for l in body:
    pa = [x.strip() for x in l.split(",")]
    rn, name = int(pa[0]), pa[1]
    em, sc = status.get((rn, norm(name)), (None, None))
    already = len(pa) > 2 and pa[2].upper().startswith("SCR")
    if em is None and not already:
        unknown.append(f"R{rn} {name}")
    fk_open = next((x for x in pa[2:] if x.startswith("fk_open")), None)
    if already or sc or (em and not race_morning):
        res.append(l if already else f"{rn}, {name}, SCR" + (f", {fk_open}" if fk_open else "")); n_scr += 1
    else:
        res.append(l); n_in += 1
        if em: em_in.append(f"R{rn} {name}")
open(out, "w").write("\n".join(res) + "\n")
print(f"{out.split('/')[-1]} priced {n_in} SCR {n_scr} emergencies in: {em_in}"
      + ("" if race_morning else " (not race morning: every emergency SCR)"))
if unknown:
    print(f"WARNING: not in the entry numbers (check the spelling or re-pull the numbers): {unknown}")
