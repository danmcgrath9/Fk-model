"""Take-at list for a meeting with no market yet: every runner the rules allow, with the price to take and the stake at
that price. python takeat_list.py DAYPREFIX GOING [ALT_GOING] > out.md   (run from data/live_bets or give full paths)"""
import json, sys, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stake_rule
pre, G = sys.argv[1], sys.argv[2]; G2 = sys.argv[3] if len(sys.argv) > 3 else None
scr = {(int(l.split(',')[0]), l.split(',')[1].strip()) for l in open(f"{pre}-prices.txt") if l[0].isdigit() and 'SCR' in l}
def load(g):
    v = [r for r in json.load(open(f"{pre}-{g}-v6.json")) if (r['race'], r['horse']) not in scr]
    t = defaultdict(float)
    for r in v: t[r['race']] += r['p']
    for r in v: r['pp'] = r['p'] / t[r['race']]
    fu = json.load(open(f"{pre}-{g}-first-up-blocks.json"))
    return v, {k.split('|', 1)[1] for k in json.load(open(f"{pre}-{g}-first-starters.json"))}, \
        {k.split('|', 1)[1] for k, x in fu.items() if not x.startswith('EARLY')}, {k.split('|', 1)[1] for k, x in fu.items() if x.startswith('EARLY')}
v, fs, blk, ear = load(G)
alt = {(r['race'], r['horse']): 1 / r['pp'] for r in load(G2)[0]} if G2 else {}
fsr = {int(k.split('|')[0]) for k in json.load(open(f"{pre}-{G}-first-starters.json"))}
R = defaultdict(list)
for r in v: R[r['race']].append(r)
print(f"| Race | Horse | Ours ({G}) | Take at | Stake at take-at |" + (f" Ours ({G2}) |" if G2 else "") + " Note |")
print("|---|---|---|---|---|" + ("---|" if G2 else "") + "---|")
for rc in sorted(R):
    n = len(R[rc])
    for r in sorted(R[rc], key=lambda r: -r['pp']):
        h = r['horse']; pp = r['pp']; pr = 1 / pp
        if pr < 1.6 or pr > 15 or h in fs or h in blk: continue
        take = pr * 1.2; note = []
        if h in ear:
            if take > 8: continue
            note.append('EARLY')
        if rc in fsr: note.append('FS race')
        if r.get('only_ride'): note.append('ONLY RIDE')
        if n <= 8: note.append(f'field {n}')
        a = alt.get((rc, h))
        print(f"| R{rc} | {h} | ${pr:.2f} | ${take:.2f} | {stake_rule.stake(pp, take, r.get('only_ride', False), n)}u |" + ((f" ${a:.2f} |" if a else " - |") if G2 else "") + f" {', '.join(note)} |")
