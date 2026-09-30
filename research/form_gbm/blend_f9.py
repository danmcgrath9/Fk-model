import numpy as np, bench as b
D=b.load(); nR=D["n_races"]; allr=np.arange(nR)
t,n,c=np.load("p_oof_f9.npy"),np.load("p_oof9_nn.npy"),np.load("p_oof9_cb.npy")
bl=b.softmax_races(0.5*np.log(t)+0.3*np.log(n)+0.2*np.log(c)); np.save("p_oof_blend9.npy",bl)
for nm,p in [("trees9",t),("net9",n),("cb9",c),("blend9",bl),("blend (live)",np.load("p_oof_blend3.npy"))]: print(b.fmt(nm,b.score(p,allr)))
