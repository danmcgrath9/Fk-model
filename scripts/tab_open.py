"""Record TAB opening prices (read off the founder's screenshots) into a meeting's prices file.
    python scripts/tab_open.py data/live_bets/2026-10-15-warrnambool-prices.txt TAB.txt
TAB.txt is one runner per line, "race, horse, price" (e.g. "3, Katoto, 9.50"); # starts a comment.
Each price is written as "tab_open X" in the runner's fifth field, beside Form King's "fk_open" (see
research/form_gbm/opens.py). A horse is matched by race and letters only, so "Knock Of Beers" and "knock of beers" match.
Prints every line it could NOT place, and never touches a scratched runner. A TAB open already recorded is NOT
overwritten (the open is the first price, and a second screenshot is a later price); pass --force to correct a typo."""
import re, sys
args = [a for a in sys.argv[1:] if a != "--force"]; force = "--force" in sys.argv
pt, tf = args
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
tab = {}
for l in open(tf):
    l = l.split("#")[0].strip()
    if not l: continue
    pa = [x.strip() for x in l.split(",")]
    if len(pa) != 3 or not pa[0].isdigit(): sys.exit(f"bad line (want 'race, horse, price'): {l}")
    tab[(int(pa[0]), norm(pa[1]))] = (pa[1], float(pa[2]))
out, used, kept = [], set(), []
for l in open(pt):
    body, _, cmt = l.rstrip("\n").partition("#")
    pa = [x.strip() for x in body.split(",")]
    if len(pa) >= 3 and pa[0].isdigit():
        k = (int(pa[0]), norm(pa[1]))
        if k in tab and not pa[2].upper().startswith("SCR"):
            used.add(k)
            while len(pa) < 5: pa.append("")
            if "tab_open" in pa[4] and not force: kept.append(f"R{k[0]} {pa[1]} ({pa[4]})")
            else:
                f5 = re.sub(r"\s*tab_open\s+[\d.]+", "", pa[4]).strip()
                pa[4] = (f5 + " " if f5 else "") + f"tab_open {tab[k][1]:.2f}"
            l = ", ".join(pa) + (" #" + cmt if cmt else "")
    out.append(l)
open(pt, "w").write("\n".join(out) + "\n")
print(f"recorded {len(used) - len(kept)} TAB opens in {pt}")
for s in kept: print(f"  kept the TAB open already recorded: {s}")
for k, (h, p) in tab.items():
    if k not in used: print(f"  NOT PLACED (no such runner, or scratched): R{k[0]} {h} ${p:.2f}")
