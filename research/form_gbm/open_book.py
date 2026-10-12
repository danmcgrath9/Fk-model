"""The open-price shadow book (12 Oct 2026, founder: "let's keep track of that for our bets"). For a priced meeting,
the bets the live rules would have struck at Form King's OPENING price (every runner's price set to its open), so we
can settle what being on at the open was worth beside what we actually took.
    python open_book.py DAYPREFIX GTAG      e.g. 2026-10-14-caulfield g4
Writes data/live_bets/DAYPREFIX-GTAG-open-bets.csv and appends the bets, unsettled, to data/live_bets/open-book.md."""
import csv, os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(here, "../../data/live_bets")
pre, g = sys.argv[1:3]; B = f"{L}/{pre}-{g}"
lines = []
for l in open(f"{L}/{pre}-prices.txt"):
    pa = [x.strip() for x in l.split("#")[0].split(",")]
    m = re.search(r"([\d.]+)\s*$", pa[4]) if len(pa) >= 5 and pa[0].isdigit() else None
    lines.append(f"{pa[0]}, {pa[1]}, {m.group(1)}, {m.group(1)}, {pa[4]}" if m else l.rstrip("\n"))
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
                          "| Meeting | Race | Horse | Open | Ours | Stake | Result | SP | P/L (u) |\n|---|---|---|---|---|---|---|---|---|\n")
label = f"{pre[:10]} {pre[11:].title()} ({g.upper()})"
have = open(book).read()
with open(book, "a") as fh:
    for r in rows:
        line = f"| {label} | R{r['race']} | {r['horse']} | ${float(r['open']):g} | ${float(r['model_price']):.2f} | {float(r['stake']):g}u | | | |\n"
        if line not in have: fh.write(line)
print(f"{label}: {len(rows)} bets at the open, {sum(float(r['stake']) for r in rows):.2f}u")
for r in rows: print(f"  R{r['race']} {r['horse']} open ${float(r['open']):g} ours ${float(r['model_price']):.2f} {float(r['stake']):g}u")
