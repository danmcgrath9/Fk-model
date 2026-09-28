import numpy as np, html, json, sys, bench as b, price_day as pdm
title, out = sys.argv[1], sys.argv[2]
D, nR, U, _ = pdm.combined(); pdm.install(D)
F, nm = pdm.inputs(); p = pdm.predict(F, nR, nm)
n0 = len(D["race_idx"]) - len(U["race_idx"])
ci = {n: j for j, n in enumerate(nm)}
rows = []
for i in range(n0, len(D["race_idx"])):
    starts = F[i, ci["f_careerForm_s"]]; solid = bool((np.nan_to_num(starts, nan=-1) >= 1) and not np.isnan(F[i, ci["e_speedRating_last"]]) and F[i, ci["age"]] != 2)
    r = D["race_idx"][i] - nR
    rows.append(dict(race=int(U["race_number"][r]), race_id=str(U["race_id"][r]), horse=str(D["name"][i]), horse_id=str(D["horse_id"][i]),
                     barrier=None if np.isnan(D["X"][i, D["colidx"]["barrier"]]) else int(D["X"][i, D["colidx"]["barrier"]]),
                     jockey=str(D["jockey"][i]), p=float(p[i]), solid=solid))
json.dump(rows, open(out.replace(".html", ".json"), "w"), indent=1)
css = """
:root{--bg:#f4f6f3;--ink:#16211a;--mute:#5b675e;--line:#d5ddd4;--card:#fff;--acc:#1f6b3d;--hl:#e8f2ea}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#101511;--ink:#e5ebe5;--mute:#98a59a;--line:#29322b;--card:#161e18;--acc:#6fcf8e;--hl:#1c2b20}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#101511;--ink:#e5ebe5;--mute:#98a59a;--line:#29322b;--card:#161e18;--acc:#6fcf8e;--hl:#1c2b20}
body{background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif;padding-inline:16px;padding-block:20px 40px}
.wrap{max-width:860px;margin:0 auto;display:grid;gap:18px;grid-template-columns:minmax(0,1fr)}
h1{font-size:26px;margin:0} h2{font-size:18px;margin:0 0 6px} .sub{color:var(--mute);margin:4px 0 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-width:0}
.scroll{overflow-x:auto} table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap} th{color:var(--mute);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.l{text-align:left} tr.top td{background:var(--hl);font-weight:600}
"""
h = [f"<title>{html.escape(title)}</title><style>{css}</style><div class='wrap'><header><h1>{html.escape(title)}</h1>",
     "<p class='sub'>Model price: Form King inputs only, no market (trees + regression + neural net). Take at 20c = the price for 20c of value (level-stake plan). Take at 5c = where quarter Kelly starts. Best-bet rule = the narrow plan that held up on the holdout: a horse that has raced, has speed figures and is not a 2yo, at 50c+ of value and $3 to $20; or under $3 at 10c+ of value.</p></header>"]
for rn in sorted({x["race"] for x in rows}):
    rs = sorted([x for x in rows if x["race"] == rn], key=lambda x: -x["p"])
    h.append(f"<section class='card'><h2>Race {rn}</h2><div class='scroll'><table><tr><th class='l'>Horse</th><th>Bar</th><th class='l'>Jockey</th><th>Chance</th><th>Model $</th><th>Take at 5c</th><th>Take at 20c</th><th>Best-bet rule: take at</th></tr>")
    for k, x in enumerate(rs):
        fair = 1 / x["p"]
        if fair * 1.1 < 3: rule = f"${fair*1.1:.2f}+ (under-$3 rule)"
        elif x["solid"] and 3 <= fair * 1.5 <= 20: rule = f"${fair*1.5:.2f} to $20"
        else: rule = ""
        h.append(f"<tr class='{'top' if k < 2 else ''}'><td class='l'>{html.escape(x['horse'])}</td><td>{x['barrier'] or ''}</td><td class='l'>{html.escape(x['jockey'])}</td>"
                 f"<td>{x['p']:.1%}</td><td>${fair:.2f}</td><td>${fair*1.05:.2f}</td><td>${fair*1.2:.2f}</td><td>{rule}</td></tr>")
    h.append("</table></div></section>")
h.append("</div>")
open(out, "w").write("\n".join(h))
for rn in sorted({x["race"] for x in rows}):
    rs = sorted([x for x in rows if x["race"] == rn], key=lambda x: -x["p"])[:3]
    print(rn, [(x["horse"], round(1 / x["p"], 2)) for x in rs])
