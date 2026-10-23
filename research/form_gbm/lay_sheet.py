"""Paper lay sheet for a race day (rule fixed 23 Oct 2026, data/live_bets/betmatic-book.md "Paper lay book"):
lay at Betfair SP if BSP is $15-$30 AND at least 1.6x our price. Our price = the live shaded model (p_model: stage 2,
back-settler shade, before the blend with the open). First starters and runners with no Australian form held
(internationals) are excluded. Only runners whose trigger is $30 or under can qualify (ours $18.75 or shorter).
python lay_sheet.py DAYPREFIX GTAG NPZ  (prints one CSV row per runner with a trigger)"""
import json, re, sys, numpy as np
L = "/home/user/fk-model/data/live_bets"; pre, g, npz = sys.argv[1:4]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
rows = json.load(open(f"{L}/{pre}-{g}-v6.json")); fs = json.load(open(f"{L}/{pre}-{g}-first-starters.json"))
fsk = {norm(x.split("|")[-1]) if isinstance(x, str) else norm(str(x)) for x in (fs if isinstance(fs, list) else fs.keys())}
px = {}
for l in open(f"{L}/{pre}-prices.txt"):
    pa = [x.strip() for x in l.split("#")[0].split(",")]
    if len(pa) >= 3 and pa[0].isdigit() and pa[2].upper() != "SCR": px[(int(pa[0]), norm(pa[1]))] = pa[2]
U = np.load(npz, allow_pickle=True); c = list(U["cols"]); f = {str(x): i for i, x in enumerate(U["past_fields"])}
held = {norm(str(n)): bool(np.isfinite(U["P"][i, :, f["finish"]]).any()) for i, n in enumerate(U["name"])}
starts = {norm(str(n)): float(np.nan_to_num(U["X"][i, c.index("f_careerForm_s")], nan=0)) for i, n in enumerate(U["name"])} if "f_careerForm_s" in c else {}
by = {}
for r in rows: by.setdefault(r["race_id"], []).append(r)
print("race,horse,ours,lay_if_bsp_at_least,lay_if_bsp_at_most,price_now,note")
for rid, rs in sorted(by.items(), key=lambda t: t[1][0]["race"]):
    s = sum(r["p_model"] for r in rs)
    for r in sorted(rs, key=lambda r: -r["p_model"]):
        ours = s / r["p_model"]; trig = max(15.0, 1.6 * ours)
        if trig > 30: continue
        k = norm(r["horse"]); note = ""
        if k in fsk: note = "first starter: excluded"
        elif not held.get(k, True): note = "no Australian form held (international): excluded"
        now = px.get((r["race"], k), "")
        print(f'{r["race"]},{r["horse"]},{ours:.2f},{trig:.2f},30,{now},{note}')
