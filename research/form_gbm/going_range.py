"""Track-range caveats (6 Oct 2026). When the track call is a range (e.g. 'G4 to S6'), the day is priced at
both ends and this adds a short note to the top of the market sheet naming ONLY the bets the track changes:
a bet at one end only (bet it only if the track is that end), or a stake that differs by 1u or more between
the ends (the stake for each). Bets the track does not change get no note.
python going_range.py PAGE_HTML LABEL_A BETS_A NPZ_A LABEL_B BETS_B NPZ_B"""
import csv, html, re, sys
import numpy as np

page, la, ba, na, lb, bb, nb = sys.argv[1:8]


def bets(path):
    out = {}
    for r in csv.DictReader(open(path)):
        if r["plan"] == "top_pick":
            continue
        k = (int(r["race"]), r["horse"])
        s = float(r["stake"])
        if k not in out or s > out[k]["stake"]:
            out[k] = {"stake": s, "price": float(r["price"]), "ours": float(r["model_price"])}
    return out


def records(npz):
    U = np.load(npz, allow_pickle=True)
    c = {str(x): i for i, x in enumerate(U["cols"])}
    X = U["X"]
    g = lambda i, k: int(X[i, c[k]]) if np.isfinite(X[i, c[k]]) else 0
    return {str(n): (g(i, "f_goingForm_good_s"), g(i, "f_goingForm_good_w"), g(i, "f_goingForm_slow_s"), g(i, "f_goingForm_slow_w"),
                     g(i, "f_heavyForm_s"), g(i, "f_heavyForm_w")) for i, n in enumerate(U["name"])}


A, B, rec = bets(ba), bets(bb), records(na)
rows = []
for k in sorted(set(A) | set(B)):
    a, b = A.get(k), B.get(k)
    if a and b and abs(a["stake"] - b["stake"]) < 1:
        continue
    if a and b:
        do = (f"{a['stake']:.1f}u on a {la} (ours ${a['ours']:.2f}), {b['stake']:.1f}u on a {lb} (ours ${b['ours']:.2f}). "
              f"Bet {b['stake'] if 'soft' in lb.lower() else a['stake']:.1f}u unless the track is {la if 'soft' in lb.lower() else lb}.")
    elif a:
        do = f"Bet only on a {la} ({a['stake']:.1f}u, ours ${a['ours']:.2f}). No bet on a {lb}."
    else:
        do = f"Bet only on a {lb} ({b['stake']:.1f}u, ours ${b['ours']:.2f}). No bet on a {la}."
    gs, gw, ss, sw, hs, hw = rec.get(k[1], (0,) * 6)
    rc = f"Wins: good {gw} from {gs}, soft {sw} from {ss}, heavy {hw} from {hs}."
    rows.append(f"<li><b>R{k[0]} {html.escape(k[1])}:</b> {do} {rc}</li>")
    print(f"R{k[0]} {k[1]}: {do} {rc}")

box = (f"<div class='rng'><b>Track {la} to {lb}:</b> "
       + (f"priced at both ends. The track matters for these:<ul>{''.join(rows)}</ul>" if rows
          else "priced at both ends, and no bet changes between them.") + "</div>")
css = (".rng{border:2px solid #1b1b1b;padding:12px 14px;margin:0 0 18px}.rng p{font-size:13.5px;margin:4px 0 10px}"
       ".rng{font-size:13.5px}.rng ul{margin:6px 0 0;padding-left:18px}.rng li{margin:4px 0}"
       "@media(prefers-color-scheme:dark){.rng{border-color:#eee}}")
s = open(page).read()
s = re.sub(r"<div class='rng'>.*?</table></div></div>", "", s, flags=re.S)
s = re.sub(r"<div class='rng'>.*?</div>", "", s, flags=re.S)
s = re.sub(r"\.rng\{.*?@media\(prefers-color-scheme:dark\)\{\.rng\{border-color:#eee\}[^}]*\}\}", "", s)
s = s.replace("</style>", css + "</style>", 1)
s = re.sub(r"(<div class='sub'>.*?</div>)", lambda m: m.group(1) + box, s, count=1, flags=re.S)
open(page, "w").write(s)
