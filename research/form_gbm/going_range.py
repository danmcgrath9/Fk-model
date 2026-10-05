"""Track-range caveats (6 Oct 2026). When the track call is a range (e.g. 'G4 to S6'), the day is priced at
both ends and this adds a box to the top of the market sheet saying, per bet:
  - the stake at each end of the range,
  - what to do: a bet at both ends is bet at the smaller stake; a bet at one end only is bet ONLY if the
    track is that end on the morning,
  - the horse's win record on good, soft and heavy (information, not a rule: the model already prices it).
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
    if a and b:
        do = f"Bet {min(a['stake'], b['stake']):.1f}u (${min(a['stake'], b['stake']) * 100:.0f}) either way"
    elif a:
        do = f"<b>Only if the track is {la} or better</b>: {a['stake']:.1f}u"
    else:
        do = f"<b>Only if the track is {lb} or worse</b>: {b['stake']:.1f}u"
    gs, gw, ss, sw, hs, hw = rec.get(k[1], (0,) * 6)
    rc = f"good {gw} from {gs} · soft {sw} from {ss} · heavy {hw} from {hs}"
    st = lambda x: f"{x['stake']:.1f}u at ${x['price']:.2f} (ours ${x['ours']:.2f})" if x else "no bet"
    rows.append(f"<tr><td>R{k[0]} {html.escape(k[1])}</td><td>{st(a)}</td><td>{st(b)}</td><td>{do}</td><td>{rc}</td></tr>")
    print(f"R{k[0]} {k[1]}: {la} {st(a)} | {lb} {st(b)} | {re.sub('<[^>]+>', '', do)} | {rc}")

box = (f"<div class='rng'><h2 style='margin-top:0'>Track call {la} to {lb}</h2>"
       f"<p>Priced at both ends. A bet at both ends goes on at the smaller stake. A bet at one end only goes on only if the "
       f"track is that end on race morning. The win records are for reading: the model has already priced them.</p>"
       f"<div style='overflow-x:auto'><table><tr><th>Bet</th><th>{la}</th><th>{lb}</th><th>Do</th><th>Wins on each going</th></tr>"
       + "".join(rows) + "</table></div></div>")
css = (".rng{border:2px solid #1b1b1b;padding:12px 14px;margin:0 0 18px}.rng p{font-size:13.5px;margin:4px 0 10px}"
       ".rng table{border-collapse:collapse;font-size:13px;width:100%}.rng th,.rng td{text-align:left;padding:6px 8px;"
       "border-bottom:1px solid #ddd;vertical-align:top}@media(prefers-color-scheme:dark){.rng{border-color:#eee}.rng th,.rng td{border-color:#333}}")
s = open(page).read()
s = re.sub(r"<div class='rng'>.*?</table></div></div>", "", s, flags=re.S)
s = s.replace("</style>", css + "</style>", 1) if ".rng{" not in s else s
s = re.sub(r"(<div class='sub'>.*?</div>)", lambda m: m.group(1) + box, s, count=1, flags=re.S)
open(page, "w").write(s)
