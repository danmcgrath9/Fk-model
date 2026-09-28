import numpy as np, bench as b
from datetime import date, timedelta
from collections import defaultdict
import bisect

def features():
    D = b.D; P = D["P"]; f = list(D["past_fields"]); ids = D["past_race_ids"]; hid = D["horse_id"]
    fin = P[:, :, f.index("finish")]; days = P[:, :, f.index("days_before")]; trial = P[:, :, f.index("trial")]
    ri = D["race_idx"]; rdate = np.array([date.fromisoformat(d) for d in D["date"]])[ri]
    members = defaultdict(dict)            # past race id -> {horse: finish}
    runs = defaultdict(dict)               # horse -> {date: finish}
    for i in range(len(hid)):
        for j in range(10):
            if ids[i, j] and not np.isnan(fin[i, j]) and trial[i, j] != 1 and not np.isnan(days[i, j]):
                d = rdate[i] - timedelta(days=int(days[i, j]))
                members[ids[i, j]][hid[i]] = fin[i, j]; members[ids[i, j]]["__date"] = d
                runs[hid[i]][d] = fin[i, j]
        if D["finish"][i] > 0:
            runs[hid[i]][rdate[i]] = float(D["finish"][i])     # today's result, usable by LATER races only
    rsorted = {h: sorted(v.items()) for h, v in runs.items()}
    def since(h, d0, d1):
        """(runs, wins, places) for horse h strictly after d0 and strictly before d1."""
        lst = rsorted.get(h)
        if not lst: return 0, 0, 0
        ds = [x[0] for x in lst]
        a = bisect.bisect_right(ds, d0); z = bisect.bisect_left(ds, d1)
        sub = [x[1] for x in lst[a:z]]
        return len(sub), sum(1 for x in sub if x == 1), sum(1 for x in sub if x <= 3)
    n = len(hid); keys = ("cl_beaten_runs", "cl_beaten_wins", "cl_beaten_wr", "cl_beaters_wr", "cl_race_wr", "cl_race_pr", "cl_last_race_wr", "cl_n_known")
    out = {k: np.full(n, np.nan) for k in keys}
    for i in range(n):
        T = rdate[i]; A = hid[i]
        br = bw = bp = 0; ar = aw = 0; rr = rw = rp = 0; last_wr = np.nan; known = 0; used = 0
        for j in range(10):
            if used >= 3: break
            rid = ids[i, j]
            if not rid or rid not in members or np.isnan(fin[i, j]) or trial[i, j] == 1: continue
            used += 1
            m = members[rid]; d0 = m["__date"]; fa = fin[i, j]
            lr = lw = 0
            for B, fb in m.items():
                if B in ("__date", A): continue
                r_, w_, p_ = since(B, d0, T)
                if r_ == 0: continue
                known += 1; rr += r_; rw += w_; rp += p_; lr += r_; lw += w_
                if fb > fa: br += r_; bw += w_
                else: ar += r_; aw += w_
            if used == 1 and lr: last_wr = lw / lr
        out["cl_beaten_runs"][i] = br; out["cl_beaten_wins"][i] = bw
        out["cl_beaten_wr"][i] = bw / br if br else np.nan
        out["cl_beaters_wr"][i] = aw / ar if ar else np.nan
        out["cl_race_wr"][i] = rw / rr if rr else np.nan; out["cl_race_pr"][i] = rp / rr if rr else np.nan
        out["cl_last_race_wr"][i] = last_wr; out["cl_n_known"][i] = known
    return out
