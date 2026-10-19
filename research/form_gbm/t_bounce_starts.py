"""Bounce block split by career starts (founder, 19 Oct: "a spike rating but has had less than 5 starts?").
Reuses t_blocks_audit.py's arrays (holdout from 3 Jun, p10, live order rule). Career starts = X raw_starts before today."""
import io, contextlib, numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("t_blocks_audit.py").read())
cs = D["X"][:, cols.index("raw_starts")].astype(float)
print("raw_starts sample among bounce runners:", np.nanpercentile(cs[bounce & base], [0, 25, 50, 75, 100]))
print("nreal (history rows) sample:", np.percentile(nreal[bounce & base], [0, 25, 50, 75, 100]))
st = stakes(ALL - {"bounce"}); d = st - live
print("| bets | n | won | staked | profit at open (ROI) | boot SE | P(profit<=0) | profit at BSP (ROI) |\n|---|---|---|---|---|---|---|---|")
print(row("ADDED by lifting bounce (all)", d, d > 1e-9))
for lab, cond in (("bounce, under 5 career starts", cs < 5), ("bounce, 5-9 starts", (cs >= 5) & (cs < 10)), ("bounce, 10+ starts", cs >= 10),
                  ("bounce, <5 starts, back within 21d", (cs < 5) & (gap <= 21)), ("bounce, <5 starts, 22+ days", (cs < 5) & (gap > 21)),
                  ("bounce, 5+ starts, back within 21d", (cs >= 5) & (gap <= 21)), ("bounce, 5+ starts, 22+ days", (cs >= 5) & (gap > 21))):
    dd = np.where(cond, d, 0); print(row(f"ADDED by lifting {lab}", dd, dd > 1e-9))
print("\nCalibration of all bounce runners by starts (won vs our sum p10, open, BSP)")
print("| group | runners | won | sum p10 | z | sum open chance | sum BSP chance |\n|---|---|---|---|---|---|---|")
for lab, cond in (("bounce <5 starts", cs < 5), ("bounce 5+ starts", cs >= 5), ("non-bounce <5 starts", ~bounce & (cs < 5) & has)):
    print(calib(lab, bounce & cond if "non" not in lab else cond))
