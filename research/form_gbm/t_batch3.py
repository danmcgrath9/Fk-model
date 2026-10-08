import numpy as np
exec(open("t_batch2.py").read().split("\nV=[")[0])
for lab,PP,M_ in (("HOLDOUT",p,hm),("BEFORE",po_,pre)):
    P_=shade(PP)
    L_,S_=var(P_,M_,mo=2,ms=1.5,recap=8); n,inv,(a,b,cc),dd=report(L_,S_)
    print(f"  {lab} only-ride x2 + field<=8 x1.5, max 8u: invested ${inv:>9,.0f}  open ${a:>+9,.0f} {a/inv*100:+5.1f}%  open-7% {b/inv*100:+5.1f}%  BSP ${cc:>+8,.0f} {cc/inv*100:+5.1f}%  DD ${dd:>7,.0f}")
    m=L_&(onlyride==1)&(field<=8)
    print(f"  {lab} overlap (only ride AND field<=8): {m.sum()} bets, strike {won[m].mean()*100:.1f}%, open ROI {roi(m,S_,pw_o):+.1f}%, BSP ROI {roi(m,S_,pw_b):+.1f}%")
