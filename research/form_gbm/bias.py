import numpy as np, bench as b, rolling
from datetime import date
def features():
    D = b.D; ri = D["race_idx"]; c = D["colidx"]; X = D["X"]; n = len(ri)
    day = np.array([(date.fromisoformat(d) - date(2020, 1, 1)).days for d in D["date"]])[ri]
    trk = D["track"][ri]; dist = D["distance"][ri]
    db = np.where(dist <= 1100, "s", np.where(dist <= 1400, "m", np.where(dist <= 1800, "l", "x")))
    field = D["field"][ri].astype(float)
    bar = X[:, c["barrier"]]; bshare = (bar - 1) / np.maximum(field - 1, 1)
    bb = np.where(np.isnan(bar), "", np.where(bshare < 0.34, "in", np.where(bshare < 0.67, "mid", "out")))
    pos = X[:, c["sm_predicted_position"]]; pshare = (pos - 1) / np.maximum(field - 1, 1)
    pb = np.where(np.isnan(pos), "", np.where(pos == 1, "lead", np.where(pshare < 0.34, "on", np.where(pshare < 0.67, "mid", "back"))))
    go = D["going"][ri].astype("U3")
    win = (D["finish"] == 1).astype(float); exp = D["q"]; ok = D["finish"] > 0
    def key(*parts):
        k = parts[0].astype("U40")
        for p in parts[1:]: k = np.char.add(np.char.add(k, "|"), p.astype("U40"))
        return np.where(np.any([p == "" for p in parts], 0), "", k)
    out = {}
    for name, k in (("bias_tdb", key(trk, db, bb)), ("bias_tdp", key(trk, db, pb)), ("bias_gp", key(go, pb)), ("bias_db", key(db, bb)),
                    ("bias_trk_pos", key(trk, pb))):
        kk = np.where(ok, k, "")
        r, w, x = rolling.roll(kk, day, win, exp, k, day)
        out[f"{name}_ae"] = np.where(r >= 10, (w + 2) / (x + 2), np.nan); out[f"{name}_n"] = np.log1p(r)
    return out
