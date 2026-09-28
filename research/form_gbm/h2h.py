import numpy as np, bench as b
def features():
    D = b.D; ids = D["past_race_ids"]; P = D["P"]; f = list(D["past_fields"])
    fin = P[:, :, f.index("finish")]; mar = P[:, :, f.index("margin")]; days = P[:, :, f.index("days_before")]
    n = len(ids); out = {k: np.full(n, np.nan) for k in ("h_net", "h_meet", "h_net_rw", "h_beat_share", "h_margin_net", "h_beat_fav")}
    for r in range(D["n_races"]):
        s, e = D["starts"][r], D["ends"][r]
        if e - s < 2: continue
        # map race id -> list of (runner, finish, margin, days)
        seen = {}
        for i in range(s, e):
            for j in range(10):
                rid = ids[i, j]
                if rid and not np.isnan(fin[i, j]):
                    seen.setdefault(rid, []).append((i, fin[i, j], mar[i, j], days[i, j]))
        net = np.zeros(e - s); meet = np.zeros(e - s); rw = np.zeros(e - s); mnet = np.zeros(e - s)
        for rid, lst in seen.items():
            if len(lst) < 2: continue
            for a in lst:
                for c in lst:
                    if a[0] == c[0]: continue
                    ahead = 1.0 if a[1] < c[1] else -1.0
                    wgt = 0.5 ** (a[3] / 180.0)
                    net[a[0] - s] += ahead; meet[a[0] - s] += 1; rw[a[0] - s] += ahead * wgt
                    ma = 0.0 if a[1] == 1 else (a[2] if not np.isnan(a[2]) else 0.0)
                    mc = 0.0 if c[1] == 1 else (c[2] if not np.isnan(c[2]) else 0.0)
                    mnet[a[0] - s] += np.clip(mc - ma, -10, 10)
        out["h_net"][s:e] = net; out["h_meet"][s:e] = meet; out["h_net_rw"][s:e] = rw
        out["h_beat_share"][s:e] = np.where(meet > 0, (net / np.maximum(meet, 1) + 1) / 2, np.nan)
        out["h_margin_net"][s:e] = np.where(meet > 0, mnet / np.maximum(meet, 1), np.nan)
    # jockey change and jockey quality
    jk = D["jockey"]; pj = D["past_jockeys"]
    out["j_same_as_last"] = np.where(pj[:, 0] == "", np.nan, (pj[:, 0] == jk).astype(float))
    out["j_rode_before"] = np.where(pj[:, 0] == "", np.nan, (pj == jk[:, None]).any(1).astype(float))
    del out["h_beat_fav"]
    return out
