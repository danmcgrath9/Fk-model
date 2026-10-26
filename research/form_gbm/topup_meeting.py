"""30-90 min after-open top-ups for one meeting from fluc_meeting.py output + the meeting's v6 json.
python3.13 topup_meeting.py CSV V6JSON FIRST_STARTERS_JSON 'held horse;held horse'"""
import sys, csv, json, collections, stake_rule
L = open(sys.argv[1]).read().split("CSV-BEGIN")[1].split("CSV-END")[0].strip().splitlines()
R = list(csv.DictReader(L)); V = {(x["race_id"], x["horse_id"]): x for x in json.load(open(sys.argv[2]))}
FS = json.load(open(sys.argv[3])); held = {h.strip().lower() for h in sys.argv[4].split(";") if h.strip()}
print("first starters file:", str(FS)[:300])
byr = collections.defaultdict(list)
for r in R:
    if r["scratched"] == "0" and (r["race_id"], r["horse_id"]) in V: byr[r["race"]].append(r)
TIERS = (1.0, 1.25, 1.5); W = ("m30", "m40", "m45", "m50", "m60", "m90")
def stake(p, t0, E=1.3):
    q = 1 / p
    if not (1.6 <= q <= 15) or t0 >= 3 * q: return 0.0, None
    mo = 0.95 * (E / p ** 0.82) ** (1 / 0.78)
    if t0 < mo: return 0.0, mo
    ts = [mo * k for k in TIERS if mo * k < 3 * q]; tot = prev = 0.0
    for k, t in enumerate(ts):
        tp = ts[k + 1] if k + 1 < len(ts) else t
        s_ = stake_rule.stake(p ** 0.82 * tp ** -0.22, tp); add = max(0.0, s_ - prev); prev = max(prev, s_)
        if t0 >= t: tot += add
    return tot, mo
print("\n| race | horse | ours | open | first time it fired | avg then | best est. | min (take if still) | book units | Twitter | best books now | avg now |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for rn in sorted(byr, key=int):
    xs = byr[rn]; s = sum(float(V[(x["race_id"], x["horse_id"])]["p_model"]) for x in xs)
    for x in xs:
        p = float(V[(x["race_id"], x["horse_id"])]["p_model"]) / s
        if x["name"].strip().lower() in held or not x["open"]: continue
        op = float(x["open"]); ratio = (float(x["best_now"]) / float(x["avg_now"])) if x["best_now"] and x["avg_now"] else 1.0
        for c in W:
            if not x[c]: continue
            t = float(x[c])
            if t / op >= 1.2: continue
            st, mo = stake(p, t * ratio)
            if st > 0:
                print(f"| R{rn} | {x['name']} | ${1/p:.2f} | ${op:g} | {c[1:]} min | ${t:g} | ${t*ratio:.2f} | ${mo:.2f} | {st:.2f}u | {min(5, st/2):.2f}u | {x['best_bookies'][:40]} ${x['best_now']} | ${x['avg_now']} |")
                break
