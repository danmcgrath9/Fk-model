import numpy as np
exec(open('t_m3.py').read().split('import sys')[0])
o_orig=o.copy()
pm,ins=samples['HOLD']; base=ins&race_ok[ri]&np.isfinite(bs)
bk=np.bincount(ri,weights=np.where(okp,1/np.where(okp,o_orig,1),0),minlength=nR)
races=len(np.unique(ri[base]))
for target in (None,1.25,1.28):
    if target is None: o[:]=o_orig
    else:
        scale=np.where(bk[ri]>0, bk[ri]/target, 1.0)      # shorten every open in the race so its book is `target`
        o[:]=np.maximum(1.01, 1+(o_orig-1)*1.0)*np.where(bk[ri]<target, scale, 1.0)
    r=run(pm,ins,1.2); st=sum(x[1] for x in r); pl=sum(x[2] for x in r)
    print(f"opening book {'as recorded (median 1.19)' if target is None else f'raised to {target:.2f} where lower'}: {len(r)} bets ({len(r)/races:.2f}/race), {st:.0f}u, {pl:+.0f}u ({100*pl/st:+.1f}%)")
