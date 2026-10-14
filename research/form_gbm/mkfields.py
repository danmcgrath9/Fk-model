"""prices-fields file from entry_numbers.py output: every runner at 0 price, emergencies and scratchings as SCR.
usage: mkfields.py NUMS OUT HEADER"""
import sys
nums, out, head = sys.argv[1:4]
rows = [l.strip().split('|') for l in open(nums) if l.count('|') == 4 and l[0].isdigit()]
res = [head]
for rn, num, name, em, sc in sorted(rows, key=lambda r: (int(r[0]), int(r[1]) if r[1].isdigit() else 99)):
    res.append(f"{rn}, {name}, SCR" if em == 'True' or sc == 'True' else f"{rn}, {name}, 0, 0")
open(out, 'w').write('\n'.join(res) + '\n')
print(out.split('/')[-1], 'runners', sum('SCR' not in x for x in res[1:]), 'SCR', sum('SCR' in x for x in res[1:]))
