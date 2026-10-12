"""The open-price shadow book (12 Oct 2026, founder: "let's keep track of that for our bets"). For a priced meeting,
the bets the live rules would have struck at Form King's OPENING price (every runner's price set to its open), so we
can settle what being on at the open was worth beside what we actually took.
    python open_book.py DAYPREFIX GTAG      e.g. 2026-10-14-caulfield g4
Writes data/live_bets/DAYPREFIX-GTAG-open-bets.csv and appends the bets, unsettled, to data/live_bets/open-book.md.
The book records BOTH opens (Form King's and the TAB's, see opens.py); the bets are struck on Form King's open, the TAB's when
Form King has none. A bet already in the book is never re-written by a later run (taken is taken): fill a late TAB open in by hand."""
import csv, os, re, subprocess, sys, tempfile
from opens import open_used
here = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(here, "../../data/live_bets")
pre, g = sys.argv[1:3]; B = f"{L}/{pre}-{g}"
lines = []
for l in open(f"{L}/{pre}-prices.txt"):
    pa = [x.strip() for x in l.split("#")[0].split(",")]
    v = open_used(pa[4])[0] if len(pa) >= 5 and pa[0].isdigit() and not pa[2].upper().startswith("SCR") else None
    lines.append(f"{pa[0]}, {pa[1]}, {v}, {v}, {pa[4]}" if v else l.rstrip("\n"))
tp = tempfile.mktemp(suffix=".txt"); open(tp, "w").write("\n".join(lines) + "\n")
out = f"{B}-open-bets.csv"
subprocess.run([sys.executable, os.path.join(here, "paper_open.py"), f"{B}-v6.json", tp, f"{B}-angles.json", out, "",
                f"{B}-first-starters.json", f"{B}-first-up-blocks.json"], check=True, capture_output=True); os.remove(tp)
seen, rows = set(), []
for r in csv.DictReader(open(out)):
    if r["plan"] != "top_pick" and r["horse"] not in seen: seen.add(r["horse"]); rows.append(r)
book = f"{L}/open-book.md"
if not os.path.exists(book):
    open(book, "w").write("# The open-price shadow book\n\nEvery meeting, the bets the live rules would have struck at Form King's opening price "
                          "(blended price, value judged at the open), settled against the results, beside what we actually took. "
                          "Stakes from stake_rule.py at the opening price, $100 a unit.\n\n"
                          "| Meeting | Race | Horse | FK open | TAB open | Ours | Stake | Result | SP | P/L (u) |\n|---|---|---|---|---|---|---|---|---|---|\n")
label = f"{pre[:10]} {pre[11:].title()} ({g.upper()})"
have = open(book).read()
with open(book, "a") as fh:
    for r in rows:
        fk_, tab_ = (f"${float(r[c]):g}" if r.get(c) else "-" for c in ("fk_open", "tab_open"))
        head = f"| {label} | R{r['race']} | {r['horse']} |"
        line = f"{head} {fk_} | {tab_} | ${float(r['model_price']):.2f} | {float(r['stake']):g}u | | | |\n"
        if head not in have: fh.write(line)
print(f"{label}: {len(rows)} bets at the open, {sum(float(r['stake']) for r in rows):.2f}u")
for r in rows: print(f"  R{r['race']} {r['horse']} open ${float(r['open']):g} ours ${float(r['model_price']):.2f} {float(r['stake']):g}u")
