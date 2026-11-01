"""Week Mon 26 Oct - Sun 1 Nov re-run under the 1 Nov rules: orders rebuilt by betmatic_orders.py from each meeting's priced
sheet, filled at Form King's open (each order inside its own band), scratched void, settled at the price taken (no deductions)."""
import csv, re, sys, collections, glob
sys.path.insert(0, '/home/user/fk-model/research/form_gbm'); from opens import parse_opens
L = '/home/user/fk-model/data/live_bets'; S = '/tmp/claude-0/-home-user-cafe-copilot/3bac7eba-1a73-583c-b23d-aae29b750b5b/scratchpad'
nm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
res = {}
for f in ('nov/montue_results.md', 'nov/fri_sun_results.md', 'nov/sat31_meeting_results.md'):
    cur = None
    for l in open(f'{S}/{f}'):
        m = re.match(r'## ([a-z-]+?)-(\d{8})', l)
        if m: cur = m[1]; continue
        m = re.match(r'R(\d+) (.+?)\s+finish (\S+)', l)
        if m and cur: res[(cur, int(m[1]), nm(m[2]))] = m[3]
fl = {}
t = open(f'{S}/nov/sat31_fluc_meeting.md').read(); lines = [l for l in t.splitlines() if l.count(',') > 10]
R = list(csv.reader(lines)); h = R[0]
for r in R[1:]:
    if r[0] == 'race': continue
    d = dict(zip(h, r)); fl[(d['race_id'][:4], int(d['race']), nm(d['name']))] = d
code = {'mortlake': 'MORT', 'wycheproof': 'WYCH', 'healesville': 'HEAL'}
void_mtg = {'traralgon'}; void_races = {('mornington', r) for r in range(2, 10)}; res[('mornington', 1, 'starjetaime')] = '2'  # lost (founder, 1 Nov); placing not yet in Form King   # Mornington R2-R9 not yet run
tot = collections.OrderedDict(); allw = 0
for f in sorted(glob.glob(f'{S}/week/2026-*.csv')):
    P = f.split('/')[-1][:-4]; mt = P[11:]
    op, scr = {}, set()
    if mt in code:
        for (c, rc, n), d in fl.items():
            if c == code[mt]:
                if d.get('scratched') == '1': scr.add((rc, n))
                elif d.get('open'): op[(rc, n)] = float(d['open'])
    else:
        for l in open(f'{L}/{P}-prices.txt'):
            pa = [x.strip() for x in l.split('#')[0].split(',')]
            if len(pa) >= 3 and pa[0].isdigit():
                if pa[2].upper().startswith('SCR'): scr.add((int(pa[0]), nm(pa[1]))); continue
                a, b = parse_opens(', '.join(pa[3:])); x = a or b
                if x: op[(int(pa[0]), nm(pa[1]))] = x
    H = collections.OrderedDict()
    for o in csv.DictReader(open(f)):
        k = (int(o['race']), nm(o['horse'])); x = op.get(k)
        if k in scr or x is None or not (float(o['min_odds']) <= x < float(o['max_odds'])): continue
        hh = H.setdefault(k, dict(horse=o['horse'], st=0.0, op=x)); hh['st'] += float(o['stake_units'])
    st = pl = 0.0; w = n = 0; lines_ = []
    for (rc, _), hh in H.items():
        if (mt, rc) in void_races: lines_.append(f"    R{rc} {hh['horse']:22s} ${hh['op']:<6g} {hh['st']:5.2f}u  to run"); continue
        fin = res.get((mt, rc, nm(hh['horse'])))
        if mt in void_mtg or fin is None or fin == 'None':
            lines_.append(f"    R{rc} {hh['horse']:22s} ${hh['op']:<6g} {hh['st']:5.2f}u  {'void (abandoned)' if mt in void_mtg else 'no result'}"); continue
        p = hh['st'] * (hh['op'] - 1) if fin == '1' else -hh['st']; st += hh['st']; pl += p; n += 1; w += fin == '1'
        lines_.append(f"    R{rc} {hh['horse']:22s} ${hh['op']:<6g} {hh['st']:5.2f}u  {'WON' if fin == '1' else fin:>3s} {p:+7.2f}u")
    tot[P] = (n, w, st, pl)
    print(f"{P}: {n} bets, {w} won, {st:.2f}u, {pl:+.2f}u"); print("\n".join(lines_))
n = sum(v[0] for v in tot.values()); w = sum(v[1] for v in tot.values()); st = sum(v[2] for v in tot.values()); pl = sum(v[3] for v in tot.values())
print(f"\nWEEK (settled): {n} bets, {w} won, {st:.2f}u staked, {pl:+.2f}u ({100*pl/st:+.1f}%), ${pl*50:+,.0f} at $50")
