"""The retrain queues in one table: each arm against the base arm on the same seeds, both folds, with the noise floor
(the base arm on three seed sets). A change is REAL only if KL to BSP improves in BOTH folds by more than twice the
seed noise and the winner log loss does not get worse by more than its noise.
    python3.13 report.py [results.jsonl]"""
import json, sys
import numpy as np
rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else "results.jsonl") if l.strip()]
ALL = {"A": "A all", "B": "B all"}; R = {}
for r in rows: R[(r["name"], r["fold"])] = r
def g(name, fold, k): return R[(name, fold)]["score"][ALL[fold]][k]
noise = {}
for f in "AB":
    bs_ = [n for n in ("base", "base_s10", "base_s20") if (n, f) in R]
    noise[f] = {k: (float(np.mean([g(n, f, k) for n in bs_])), float(np.std([g(n, f, k) for n in bs_], ddof=1)) if len(bs_) > 1 else float("nan")) for k in ("kl", "ll", "profit")}
print("NOISE FLOOR (the base arm on three seed sets): mean and sd")
for f in "AB": print(f"  fold {f}: KL {noise[f]['kl'][0]:.4f} +/- {noise[f]['kl'][1]:.4f}   log loss {noise[f]['ll'][0]:.4f} +/- {noise[f]['ll'][1]:.4f}   profit {noise[f]['profit'][0]:+.0f}u +/- {noise[f]['profit'][1]:.0f}u")
names = [n for n in dict.fromkeys(r["name"] for r in rows) if not n.startswith("base")]
out = []
for n in names:
    if (n, "A") not in R: continue
    d = {}
    for f in "AB":
        if (n, f) in R: d[f] = {k: g(n, f, k) - g("base", f, k) for k in ("kl", "ll", "profit")}
    out.append((n, d, R[(n, "A")].get("note", "")))
def verdict(d):
    if "B" not in d: return "fold A only"
    k = [d[f]["kl"] / max(noise[f]["kl"][1], 1e-4) for f in "AB"]; l = [d[f]["ll"] / max(noise[f]["ll"][1], 5e-4) for f in "AB"]
    if all(x < -2 for x in k) and all(x < 2 for x in l): return "BETTER in both folds"
    if all(x > 2 for x in k): return "worse in both"
    if all(x < 0 for x in k): return "better in both, inside the noise" if not all(x < -2 for x in k) else "closer to BSP, log loss worse"
    return "no gain"
print("\n| arm | what | fold A: KL / log loss / profit v base | fold B: KL / log loss / profit v base | verdict |\n|---|---|---|---|---|")
for n, d, note in sorted(out, key=lambda x: sum(v["kl"] for v in x[1].values()) / len(x[1])):
    cell = lambda f: f"{d[f]['kl']:+.4f} / {d[f]['ll']:+.4f} / {d[f]['profit']:+.0f}u" if f in d else "-"
    print(f"| {n} | {note} | {cell('A')} | {cell('B')} | {verdict(d)} |")
