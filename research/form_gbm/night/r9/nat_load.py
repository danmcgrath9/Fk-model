"""nat_load.py: read the national Betwatch pulls (scripts/betwatch_national.py) into arrays. cache -> nat.npz"""
import csv, io, sys, os, glob
import numpy as np
csv.field_size_limit(10**9)
HERE = os.path.dirname(os.path.abspath(__file__))
MAJORS = ("tab", "sportsbet", "ladbrokes", "neds", "pointsbet", "unibet", "betr")
EXTRA = ("tabtouch", "dabble", "palmerbet", "swiftbet", "betright", "picnicbet", "betdeluxe")
METRO = {"VIC": ("flemington", "caulfield", "moonee valley", "the valley", "sandown"), "NSW": ("randwick", "royal randwick", "rosehill", "canterbury", "warwick farm"),
         "QLD": ("eagle farm", "doomben"), "SA": ("morphettville",), "WA": ("ascot", "belmont"), "TAS": (), "ACT": (), "NT": ()}
f2 = lambda x: float(x) if x not in ("", None) else np.nan


def load(files):
    R = dict(date=[], state=[], track=[], race=[], number=[], name=[], scr=[], nine=[], pos=[], bsp=[], bfm=[], status=[], x9=[], last=[], jump=[], dist=[], cls=[])
    M = {f"{b}_{k}": [] for b in MAJORS for k in ("first", "ft", "0900", "t240", "t60", "t10", "t1")}
    seen = set()
    for f in files:
        s = open(f).read(); a = s.find("CSV-BEGIN") + 9; b = s.find("CSV-END")
        if b < 0: b = len(s)                                    # a run cut off by the time limit still holds its rows
        for r in csv.DictReader(io.StringIO(s[a:b].strip())):
            try:
                k = (r["date"], r["state"], r["track"], r["race"], r["number"])
                if k in seen or not r.get("last_min") and r.get("last_min") != "": continue
                seen.add(k)
                R["date"].append(r["date"]); R["state"].append(r["state"]); R["track"].append(r["track"]); R["race"].append(int(r["race"]))
                R["number"].append(int(r["number"] or 0)); R["name"].append(r["name"]); R["scr"].append(f2(r["scr_min"])); R["nine"].append(f2(r["nine_min"]))
                R["pos"].append(f2(r["pos"])); R["bsp"].append(f2(r["bsp"])); R["bfm"].append(f2(r["bf_mkt"])); R["status"].append(r["status"])
                R["last"].append(f2(r["last_min"])); R["jump"].append(r["jump_utc"]); R["dist"].append(f2(r["dist"])); R["cls"].append(r["cls"])
                R["x9"].append(r["x9"])
                for bk in MAJORS:
                    fp = r[f"{bk}_first"]
                    if fp and ":" in fp:
                        p_, t_ = fp.split(":"); M[f"{bk}_first"].append(float(p_)); M[f"{bk}_ft"].append(float(t_))
                    else:
                        M[f"{bk}_first"].append(np.nan); M[f"{bk}_ft"].append(np.nan)
                    for k2 in ("0900", "t240", "t60", "t10", "t1"): M[f"{bk}_{k2}"].append(f2(r[f"{bk}_{k2}"]))
            except (ValueError, KeyError, TypeError):
                continue
    out = {k: np.array(v) for k, v in R.items()}; out.update({k: np.array(v, float) for k, v in M.items()})
    return out


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "nat_[A-Z].md")))
    D = load(files)
    np.savez_compressed(os.path.join(HERE, "nat.npz"), **D)
    import collections
    print(len(D["date"]), "runners;", min(D["date"]), "to", max(D["date"]), "; by state:", sorted(collections.Counter(D["state"]).items(), key=lambda x: -x[1]))
