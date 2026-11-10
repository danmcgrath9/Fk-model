import numpy as np, sys
sys.argv = ["x"]
exec(open("strat1.py").read().split("HDR = ")[0])
X, cols = D["X"], list(D["cols"]); fsr = X[:, cols.index("firstStarter")] == 1
fs_in_race = np.bincount(ri, weights=fsr, minlength=nR)[ri]
I, S_, Pr = bets(ceil=99); qq = 1 / P[I]; ov = Pr / qq; u = pl(I, S_, Pr)
chb = P[I] ** 0.82 * Pr ** -0.22   # un-normalised blend weight; use the model chance for expectation instead
print("bets with no ceiling:", len(I))
def show(lab, m):
    cells = []
    for k in range(4):
        mk = m & (per[I] == k); n = int(mk.sum())
        cells.append(f"{n:3d} bets {int(won[I[mk]].sum()):2d} won {u[mk].sum():+7.1f}u" if n else "  0")
    mm = m; fl = np.where(won[I[mm]], (Pr[mm] - 1) * 0.84, -1)
    print(f"{lab:46s} | " + " | ".join(cells) + f" | all {int(mm.sum())} bets, {int(won[I[mm]].sum())} won (we expected {P[I[mm]].sum():.1f}, BSP {nl.q[I[mm]].sum():.1f}), {u[mm].sum():+.1f}u on {S_[mm].sum():.0f}u ({100*u[mm].sum()/max(S_[mm].sum(),1e-9):+.0f}%), flat {100*fl.mean():+.0f}%, median open ${np.median(Pr[mm]):.1f}, BSP/open {np.median(bs[I[mm]]/Pr[mm]):.2f}")
big = ov >= 3
show("open 3x+ our price: all", big)
show("  first starters", big & fsr[I]); show("  not a first starter", big & ~fsr[I])
show("  not FS, no first starter in the race", big & ~fsr[I] & (fs_in_race[I] == 0))
show("  not FS, 3x-4x", big & ~fsr[I] & (ov < 4)); show("  not FS, 4x-6x", big & ~fsr[I] & (ov >= 4) & (ov < 6)); show("  not FS, 6x+", big & ~fsr[I] & (ov >= 6))
show("  not FS, we price under $5", big & ~fsr[I] & (qq < 5)); show("  not FS, we price $5-$15", big & ~fsr[I] & (qq >= 5))
print()
show("open under 3x (the live book): all", ~big); show("  first starters", ~big & fsr[I]); show("  not a first starter", ~big & ~fsr[I])
show("open 2.2x-3x, not FS", (ov >= 2.2) & ~big & ~fsr[I]); show("open 1.2x-2.2x, not FS", (ov < 2.2) & ~fsr[I])
