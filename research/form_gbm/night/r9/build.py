"""r9/build.py: one cache for the 18 Nov research (founder: "You have unlimited research time for 4 hours ... get us sharper").
Aligns Betwatch's price paths (scripts/betwatch_pull.py, bw1..6.md) to the model dataset (ds/model_ds.npz), every time
in MINUTES RELATIVE TO THE JUMP (negative = before). Run from the night folder.
  tab / maj / best : price paths (t, price[, bookie]) for TAB, the best major, the best of all bookmakers
  bk9 : {bookie: price at 9:00am race day}      nine : 9:00am race day relative to the jump
GHOSTS: a runner Betwatch flags scratched, with a 9am price, whose price was still moving after 9am race day: it was in
the 9am market and did not run. The dataset holds only runners that ran, so every earlier 9am test renormalised the
race WITHOUT these horses (the rest look like overlays that are not there) and paid winners in full (TAB deducts). They
are appended after the dataset's runners: ghost=True, never bet, counted in the race's 9am market, and their market
share is the deduction off a winner in that race."""
import csv, io, pickle, re, sys, datetime as dt, collections
import numpy as np
csv.field_size_limit(10**9)
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
z = np.load("ds/model_ds.npz", allow_pickle=True)
ri = z["race_idx"]; rid = z["race_id"].astype(str); date = z["date"].astype(str)[ri]; name = z["name"].astype(str)
rno = np.array([int(r.rsplit("_", 1)[1]) for r in rid])[ri]
key = {(date[i], int(rno[i]), norm(name[i])): i for i in range(len(ri))}
n = len(ri)
P_ = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M")


def parse(r):
    j = P_(r["jump_mel"]); t0 = (P_(r["tab_first_mel"]) - j).total_seconds() / 60
    pts = [x.split(":") for x in r["path"].split(";") if ":" in x]
    o = dict(tab=(np.array([t0 + float(a_) for a_, _ in pts]), np.array([float(p_) for _, p_ in pts])), maj=None, best=None)
    for col, first, k in (("maj_path", "maj_first_mel", "maj"), ("best_path", "best_first_mel", "best")):
        if r[col] and r[first]:
            tb = (P_(r[first]) - j).total_seconds() / 60
            q = [x.split(":") for x in r[col].split(";") if x.count(":") >= 2]
            o[k] = (np.array([tb + float(x[0]) for x in q]), np.array([float(x[1]) for x in q]), [x[2] for x in q])
    d = {}
    for x in (r["bk_0900"] or "").split(";"):
        if ":" in x:
            k, v = x.rsplit(":", 1)
            try:
                if float(v) > 1: d[k] = float(v)
            except ValueError: pass
    o["bk9"] = d
    o["nine"] = (dt.datetime.strptime(r["date"] + " 09:00", "%Y-%m-%d %H:%M") - j).total_seconds() / 60
    o["scr"] = r["scratched"] == "1"
    return o


groups = collections.OrderedDict()
for f in sys.argv[1:]:
    s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
    for r in csv.DictReader(io.StringIO(s[a:b].strip())):
        if not r["jump_mel"] or not r["tab_first_mel"] or not r["path"]: continue
        try: o = parse(r)
        except ValueError: continue
        groups.setdefault((r["date"], r["track"], int(r["race"])), {})[norm(r["name"])] = (r["name"], o)
rows = [None] * n; ghosts = []; stats = collections.Counter()
for (d, trk, rc), mem in groups.items():
    idx = {nm: key.get((d, rc, nm)) for nm in mem}
    rr = [ri[i] for i in idx.values() if i is not None]
    if not rr: stats["groups with no dataset race"] += 1; continue
    r_ = collections.Counter(rr).most_common(1)[0][0]
    for nm, (nm_raw, o) in mem.items():
        i = idx[nm]
        if i is not None and ri[i] == r_:
            rows[i] = o; stats["matched"] += 1; continue
        last = max(o["tab"][0][-1], o["maj"][0][-1] if o["maj"] else -1e9, o["best"][0][-1] if o["best"] else -1e9)
        if not o["scr"]: stats["unmatched, not scratched (name mismatch?)"] += 1; continue
        if "tab" not in o["bk9"]: stats["scratched, no 9am price"] += 1; continue
        if last < o["nine"]: stats["scratched, last price move before 9am (taken as out before 9am)"] += 1; continue
        stats["ghost: in the 9am market, did not run"] += 1; ghosts.append((r_, nm_raw, o))
out = dict(rows=rows, ghosts=ghosts)
pickle.dump(out, open(sys.argv[0].replace("build.py", "r9.pkl"), "wb"), protocol=4)
print(dict(stats)); print("races with a ghost:", len({g[0] for g in ghosts}), "of", len(np.unique(ri)))
