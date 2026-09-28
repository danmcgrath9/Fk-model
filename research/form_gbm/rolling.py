import numpy as np, bench as b
from datetime import date, timedelta

def roll(ev_key, ev_day, ev_win, ev_exp, q_key, q_day):
    """For each query: (runs, wins, expected wins) over events with the same key strictly before q_day."""
    ev_key = np.asarray(ev_key); q_key = np.asarray(q_key)
    ok = ev_key != ""; ev_key, ev_day, ev_win, ev_exp = ev_key[ok], ev_day[ok], ev_win[ok], ev_exp[ok]
    uk, ek = np.unique(ev_key, return_inverse=True)
    order = np.lexsort((ev_day, ek)); ek, ed, ew, ee = ek[order], ev_day[order], ev_win[order], ev_exp[order]
    cw, ce = np.concatenate([[0], np.cumsum(ew)]), np.concatenate([[0], np.cumsum(ee)])
    starts = np.searchsorted(ek, np.arange(len(uk)))
    qi = np.searchsorted(uk, q_key); found = (qi < len(uk)) & (uk[np.minimum(qi, len(uk) - 1)] == q_key) & (q_key != "")
    runs = np.zeros(len(q_key)); wins = np.zeros(len(q_key)); expd = np.zeros(len(q_key))
    ends = np.append(starts[1:], len(ek))
    for i in np.where(found)[0]:
        k = qi[i]; s, e = starts[k], ends[k]
        pos = s + np.searchsorted(ed[s:e], q_day[i], side="left")
        runs[i] = pos - s; wins[i] = cw[pos] - cw[s]; expd[i] = ce[pos] - ce[s]
    return runs, wins, expd

def features():
    D = b.D; P = D["P"]; f = list(D["past_fields"]); ri = D["race_idx"]; n = len(ri)
    day0 = date(2020, 1, 1)
    rday = np.array([(date.fromisoformat(d) - day0).days for d in D["date"]])[ri]
    fin_p, bsp_p, days_p, tr_p = (P[:, :, f.index(k)] for k in ("finish", "bsp", "days_before", "trial"))
    hid = D["horse_id"]
    # events: dataset rows (today) + past runs, one per horse and day
    rows_win = (D["finish"] == 1).astype(float); rows_exp = D["q"]
    seen = set(); E = {"horse": [], "day": [], "win": [], "exp": [], "jockey": [], "row": []}
    for i in range(n):
        key = (hid[i], rday[i])
        if D["finish"][i] > 0 and key not in seen:
            seen.add(key); E["horse"].append(i); E["day"].append(rday[i]); E["win"].append(rows_win[i]); E["exp"].append(rows_exp[i])
            E["jockey"].append(D["jockey"][i]); E["row"].append(i)
    for i in range(n):
        for j in range(10):
            if tr_p[i, j] == 1 or np.isnan(fin_p[i, j]) or np.isnan(days_p[i, j]) or np.isnan(bsp_p[i, j]): continue
            d = rday[i] - int(days_p[i, j]); key = (hid[i], d)
            if key in seen: continue
            seen.add(key); E["horse"].append(i); E["day"].append(d); E["win"].append(float(fin_p[i, j] == 1)); E["exp"].append(1 / bsp_p[i, j])
            E["jockey"].append(D["past_jockeys"][i, j]); E["row"].append(-1)
    eh = np.array(E["horse"]); ed = np.array(E["day"]); ew = np.array(E["win"]); ee = np.array(E["exp"]); ej = np.array(E["jockey"])
    erow = np.array(E["row"]); from_rows = erow >= 0
    out = {}
    def add(name, ev_key, q_key, mask=None):
        m = np.ones(len(ev_key), bool) if mask is None else mask
        r, w, x = roll(np.asarray(ev_key)[m], ed[m], ew[m], ee[m], q_key, rday)
        out[f"{name}_runs"] = np.log1p(r); out[f"{name}_ae"] = np.where(r > 0, (w + 1) / (x + 1), np.nan)
        out[f"{name}_wr"] = np.where(r > 0, (w + 1) / (r + 10), np.nan)
    add("sire", D["sire"][eh], D["sire"]); add("damsire", D["dam_sire"][eh], D["dam_sire"])
    add("jockey", ej, D["jockey"]); add("loc", D["training_location"][eh], D["training_location"])
    # trainer and combos: dataset rows only (past runs do not say who trained the horse then)
    add("trainer", np.where(from_rows, D["trainer"][eh], ""), D["trainer"])
    add("jt", np.where(from_rows, np.char.add(np.char.add(D["jockey"][eh], "|"), D["trainer"][eh]), ""), np.char.add(np.char.add(D["jockey"], "|"), D["trainer"]))
    c = D["colidx"]; X = D["X"]
    starts = X[:, c["f_careerForm_s"]]; fs = np.nan_to_num(starts, nan=-1) == 0
    days_last = X[:, c["daysSinceLastRace"]]; fu = np.nan_to_num(days_last) >= 60
    # sire with first starters, trainer with first-uppers: events restricted to such rows
    row_fs = np.zeros(len(eh), bool); row_fs[from_rows] = fs[erow[from_rows]]
    row_fu = np.zeros(len(eh), bool); row_fu[from_rows] = fu[erow[from_rows]]
    add("sire_fs", np.where(row_fs, D["sire"][eh], ""), np.where(fs, D["sire"], ""))
    add("trainer_fu", np.where(row_fu, D["trainer"][eh], ""), np.where(fu, D["trainer"], ""))
    return out
