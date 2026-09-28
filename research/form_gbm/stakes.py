import numpy as np, bench as b
D = b.load(); p = np.load("p_oof.npy"); ri = D["race_idx"]
op = D["open"]; bsp = np.where(np.isfinite(D["bsp"]) & (D["bsp"] > 1), D["bsp"], np.nan); won = D["won"] == 1
dates = D["date"][ri]; pre = D["pre_jump"][ri]
fair = 1 / np.maximum(p, 1e-9); ev = p * op - 1
base = np.isfinite(op) & (op > 1) & (fair < 50) & (op < 3 * fair)
top = np.zeros(len(ri), bool)
for r in range(D["n_races"]):
    s, e = D["starts"][r], D["ends"][r]; top[s + np.argmax(p[s:e])] = True
def plan(name, sel, stake):
    sel = sel & np.isfinite(op) & (op > 1); st = np.where(sel, stake, 0.0)
    ret_open = np.where(sel & won, st * op, 0.0); ret_bsp = np.where(sel & won & np.isfinite(bsp), st * bsp, 0.0)
    staked = st.sum(); prof = ret_open.sum() - staked; prof_b = ret_bsp.sum() - st[sel & np.isfinite(bsp)].sum()
    # running bank in date order, worst drawdown in units
    o = np.argsort(dates[sel], kind="stable"); pl = (ret_open - st)[sel][o]; bank = np.cumsum(pl)
    dd = (np.maximum.accumulate(np.concatenate([[0], bank])) - np.concatenate([[0], bank])).max()
    months = {}
    for m, x, s_ in zip(np.array([d[:7] for d in dates[sel]]), (ret_open - st)[sel], st[sel]):
        a = months.setdefault(m, [0.0, 0.0]); a[0] += x; a[1] += s_
    pos_m = sum(1 for v in months.values() if v[0] > 0)
    live = sel & pre; ls = st[live].sum(); lp = (np.where(live & won, st * op, 0) - np.where(live, st, 0)).sum()
    print(f"| {name} | {sel.sum()} | {(sel & won).sum()} | {staked:,.0f} | {prof:+,.0f} | {prof/staked:+.1%} | {prof_b/max(st[sel & np.isfinite(bsp)].sum(),1):+.1%} | {dd:,.0f} | {pos_m}/{len(months)} | {lp:+.1f} on {ls:.0f} |")
print("| plan | bets | winners | units staked | profit at open | return at open | return at BSP | worst drawdown | months up | live-pulled races |")
print("|---|---|---|---|---|---|---|---|---|---|")
plan("Top pick, 1 unit", top & np.isfinite(op), 1.0)
plan("Top pick, to win 1 unit", top & np.isfinite(op), 1 / np.maximum(op - 1, 0.01))
for t in (0.05, 0.10, 0.20, 0.30, 0.50):
    plan(f"Value {int(t*100)}c+, 1 unit", base & (ev > t), 1.0)
plan("Value tiered: 5-10c 1u, 10-20c 2u, 20c+ 3u", base & (ev > 0.05), np.where(ev > 0.2, 3.0, np.where(ev > 0.1, 2.0, 1.0)))
plan("Value 20c+, to win 1 unit", base & (ev > 0.2), 1 / np.maximum(op - 1, 0.01))
kelly = np.clip(25 * ev / np.maximum(op - 1, 0.01), 0, 5)
plan("Quarter Kelly, 100u bank, cap 5u (5c+)", base & (ev > 0.05), kelly)
plan("Quarter Kelly, 100u bank, cap 5u (20c+)", base & (ev > 0.2), kelly)
plan("Value 20c+, rated under $10, 1 unit", base & (ev > 0.2) & (fair < 10), 1.0)
plan("Value 20c+, fields of 12 or fewer, 1 unit", base & (ev > 0.2) & (D["field"][ri] <= 12), 1.0)
plan("Value 20c+, open $2 to $15, 1 unit", base & (ev > 0.2) & (op >= 2) & (op <= 15), 1.0)
