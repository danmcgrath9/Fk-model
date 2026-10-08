"""Our market for every race, runners in price order, and under each one WHY: the model's own reasons (tree
contributions grouped into plain themes, relative to the field) plus the horse's key facts from the day file.
python market_sheet.py UP_NPZ MODEL_JSON PRICES_TXT ANG_JSON FS_JSON FU_JSON OUT_HTML TITLE SUB [TAKEN_MD]
The page opens with the bets at the prices in the file (and the bets taken, from TAKEN_MD's first table, if given)
under a race bar that stays at the top while scrolling (8 Oct 2026, founder)."""
import numpy as np, bench as b, price_day as pdm, lightgbm as lgb, json, sys, re, html
up, mj, pt, aj, fsj, fuj, out, title, sub = sys.argv[1:10]; taken_md = sys.argv[10] if len(sys.argv) > 10 else ""
BETS = []   # (race, horse, now, ours, stake, edge, early)
# metro 40c+ was tried 7 Oct 2026 and REVERTED the same day (founder): at the open it changed profit by about -$1.8k over
# both samples; it only helped at BSP, where we do not bet (t_tracks.py).
THR = 0.2
D, nR, U, _ = pdm.combined(day=up); pdm.install(D)
F, nm = pdm.inputs()
import stage2, stake_rule
S_all = np.concatenate([np.load("S_hist.npy"), U["S"]]); SF = U["sec_fields"]
TR = stage2.trials(D["P"], D["past_fields"], D["race_idx"]); SEC = stage2.sections(S_all, SF, D["P"], D["past_fields"], D["race_idx"], int(D["race_idx"].max()) + 1)
F = np.hstack([F, TR, SEC]).astype(np.float32); F[~np.isfinite(F)] = np.nan
nm = list(nm) + [f"tr_{i}" for i in range(TR.shape[1])] + [f"sec_{i}" for i in range(SEC.shape[1])]
n0 = len(D["race_idx"]) - len(U["race_idx"]); Fd = F[n0:]; rid = D["race_idx"][n0:] - nR
C = np.mean([lgb.Booster(model_file=f"all9_sm{s}.txt").predict(Fd, pred_contrib=True)[:, :-1] for s in range(5)], 0)
# relative to the race: only differences within a race move the price
for r in np.unique(rid):
    m = rid == r; C[m] -= C[m].mean(0)
THEMES = [("last start rating", r"^(e_rat_last|x_rat_wadj_last|e_vsClass_last|e_wfaRat_last|e_rat_minus_lws|raw_last$|last_rel|last_vs_lws|raw_last_vs_lws|e_raceRating_last|e_vsAllAvg_last|e_vsTrack_last|e_expected_last)"),
 ("best and recent ratings", r"^(e_rat_(max|mean3|rw|trend|std5|n)|rating_peak|raw_peak|peak|best_vs_lws|raw_best_vs_lws|x_rat_wadj_max5|e_vsClass_(max5|rw)|e_wfaRat_(rw|max5)|e_raceRating_(rw|max5)|e_vsAllAvg_(rw|max5)|e_vsTrack_(rw|max5)|e_expected_(rw|max5)|e_rat_at_|wfa|raw_wfa|benchmarkRating|raw_trend|trend_slope|x_rat_firstup_max)"),
 ("speed and sectionals", r"(speedRating|raw_speed|speed_rel|speed_best|finish_speed|finishingSpeed|last600|to600|late_gain|^sec_)"),
 ("trial form", r"(^tr_|trial)"),
 ("jockey", r"(jockey|^jt_|^j_|apprentice)"),
 ("trainer and stable", r"(trainer|^loc_)"),
 ("barrier and track bias", r"(barrier|Barriers|^bias_)"),
 ("pace and the map", r"(settle|pos800|pos_gain|^sm_|tempo|map_vs_habit|style|early_pos|no_cover|path_width|wide_back)"),
 ("fitness and prep stage", r"(days|gap_prev|runs_90|runs_365|first_up|firstUp|secondUp|thirdUp|run_in_prep|raceInPrep|x_runs_this_prep|x_is_firstup|x_n_firstup|trainer_fu|^e_fs_rw)"),
 ("distance suitability", r"(dist|Distance|mileRaces|sprintRaces|stayingRaces|longRaces|middleRaces|shortCourse)"),
 ("track condition form", r"(going|wet|heavy|good|dead|slow|fast|synthetic|^tsg_)"),
 ("weight", r"(weight|Weight)"),
 ("class of the race", r"(class|lws|prize|strength|^c_|maiden)"),
 ("how it has run against its price", r"(lbsp|beat|mkt_class|pastp|sp_bsp|x_beat_price)"),
 ("Form King Neural", r"neural"),
 ("breeding", r"(sire|damsire)"),
 ("head to head with these rivals", r"^h_"),
 ("record and consistency", r"(consist|fin_share|top3|win_rate|place_rate|careerForm|margin|beaten|unrated|rated_runs|starts|flatForm|td_win|track_win|up_win|class_win|dist_win|going_win|wet_win)"),
 ("other", r".")]
theme_of = []
for name in nm:
    for t, rx in THEMES:
        if re.search(rx, name): theme_of.append(t); break
theme_of = np.array(theme_of); tnames = [t for t, _ in THEMES]
T = np.column_stack([C[:, theme_of == t].sum(1) for t in tnames])
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
rows = json.load(open(mj)); ang = json.load(open(aj)); fs = set(json.load(open(fsj))); fu = json.load(open(fuj))
pr = {}; scr = set()
for l in open(pt):
    pa = [x.strip() for x in l.split(",")]
    if len(pa) >= 3 and pa[0].isdigit():
        k = (int(pa[0]), norm(pa[1]))
        if pa[2].upper().startswith("SCR"): scr.add(k)
        else: pr[k] = float(pa[2])
key = {(str(U["race_id"][rid[i]]), str(D["horse_id"][n0 + i])): i for i in range(len(rid))}
cols = {str(c): i for i, c in enumerate(U["cols"])}; X = U["X"]; P = U["P"].astype(float); pf = {str(n): i for i, n in enumerate(U["past_fields"])}
def facts(i, race):
    g = lambda c: float(X[i, cols[c]]) if c in cols and np.isfinite(X[i, cols[c]]) else None
    out = []
    tr = P[i, :, pf["trial"]] == 1; fin = P[i, :, pf["finish"]]; real = ~tr & np.isfinite(fin) & (fin > 0)
    idx = np.where(real)[0]
    if not len(idx): out.append("first starter")
    else:
        j = idx[0]; d = P[i, j, pf["days_before"]]; vc = P[i, j, pf["vsClass"]]; mg = P[i, j, pf["margin"]]; rn = P[i, j, pf["runners"]]; dist = P[i, j, pf["distance"]]
        s = f"last start {int(fin[j])}/{int(rn) if np.isfinite(rn) else '?'}" + (f", {mg:.1f}L" if np.isfinite(mg) and fin[j] > 1 else "") + (f" over {int(dist)}m" if np.isfinite(dist) else "") + f", {int(d)} days ago"
        if np.isfinite(vc): s += f", rated {vc:+.1f}L vs class"
        out.append(s)
        best = np.nanmax(np.where(real, P[i, :, pf["rating"]], np.nan)); lastr = P[i, j, pf["rating"]]
        if np.isfinite(best) and np.isfinite(lastr): out.append(f"rating last {lastr:.1f}, best {best:.1f}")
        st = g("f_careerForm_s"); w = g("f_careerForm_w"); p_ = g("f_careerForm_p")
        if st: out.append(f"career {int(st)}: {int(w or 0)}-{int(p_ or 0)}")
    bar = g("raw_barrier"); ssh = g("raw_settle_share")
    if bar is not None: out.append(f"barrier {int(bar)}" + (f", usually {'leads/on pace' if ssh is not None and ssh <= 0.3 else 'midfield' if ssh is not None and ssh <= 0.65 else 'back'}" if ssh is not None else ""))
    jw = g("jockeyForm_lastTwelveMonthWinPercentage"); tw = g("trainerForm_lastTwelveMonthWinPercentage")
    if jw is not None or tw is not None: out.append(f"jockey {jw:.0f}% / trainer {tw:.0f}% last 12 months" if jw is not None and tw is not None else "")
    gf = g("f_todaysGoingForm_s"); gw = g("f_todaysGoingForm_w")
    if gf: out.append(f"today's going: {int(gw or 0)} wins from {int(gf)}")
    if g("blinkers_first") == 1: out.append("blinkers first time")
    return [o for o in out if o]
def pct(c): return f"{(np.exp(c) - 1) * 100:+.0f}%"
races = {}
for r in rows:
    k = (r["race"], norm(r["horse"])); i = key.get((r["race_id"], r["horse_id"]))
    if i is None or k in scr: continue
    races.setdefault(r["race"], []).append((r, i, k))
H = [f"<title>{html.escape(title)}</title><style>body{{font:15px/1.45 -apple-system,system-ui,sans-serif;max-width:900px;margin:0 auto;padding:16px;color:#1b1b1b;background:#fff}}h1{{font-size:22px;margin:0 0 4px}}.sub{{color:#555;font-size:13px;margin-bottom:18px}}h2{{font-size:18px;margin:26px 0 8px;border-bottom:2px solid #1b1b1b;padding-bottom:4px}}.hd{{color:#555;font-size:13px;margin-bottom:10px}}.r{{display:grid;grid-template-columns:70px 1fr;gap:4px 12px;padding:10px 0;border-bottom:1px solid #e3e3e3}}.px{{font-weight:700;font-size:18px;font-variant-numeric:tabular-nums}}.nm{{font-weight:600}}.tag{{display:inline-block;font-size:11px;padding:1px 6px;border-radius:3px;margin-left:6px;vertical-align:middle;background:#eee}}.edge{{background:#1b5e20;color:#fff}}.val{{background:#2e7d32;color:#fff}}.early{{background:#e65100;color:#fff}}.no{{background:#b71c1c;color:#fff}}.why{{grid-column:2;font-size:13.5px;color:#333}}.why b{{color:#1b1b1b}}.up{{color:#1b5e20}}.dn{{color:#b71c1c}}.mk{{font-size:12px;color:#555}}@media(prefers-color-scheme:dark){{body{{background:#121212;color:#eee}}.why{{color:#ccc}}.why b{{color:#fff}}h2{{border-color:#eee}}.r{{border-color:#333}}.tag{{background:#333}}}}</style><h1>{html.escape(title)}</h1><div class='sub'>{html.escape(sub)}</div>"]
for race in sorted(races):
    rs = races[race]; tot = sum(r["p"] for r, _, _ in rs); rs.sort(key=lambda t: -t[0]["p"])
    ri_ = rid[rs[0][1]]; dist = U["distance"][ri_]; going = U["going"][ri_]
    fsb = any(k2 in fs or f"{race}|{r2['horse']}" in fs for r2, _, k2 in rs if pr.get(k2, 99) <= 6 and f"{race}|{r2['horse']}" in fs)
    H.append(f"<h2 id='r{race}'>Race {race}</h2><div class='hd'>{int(dist)}m · our market adds to 100% · {len(rs)} runners{' · <b>no bets: a first-starter at $6 or shorter</b>' if fsb else ''}</div>")
    for r, i, k in rs:
        pp = r["p"] / tot; ours = 1 / pp; now = pr.get(k); hk = f"{race}|{r['horse']}"; isfs = hk in fs; fuv = fu.get(hk, "")
        early = fuv.startswith("EARLY:"); blocked = (fuv and not early) or isfs or fsb or (early and (now or 0) > 8) or ours > 15 or ours < 1.6 or (now and now >= 3 * ours)   # bets only at our price $1.60-$15 (floor $2 until 8 Oct 2026, t_under2.py)
        a = ang.get(hk, []); tags = []
        if blocked: tags.append("<span class='tag no'>no bet</span>")
        else:
            if now and pp * now - 1 >= THR:
                stake = stake_rule.stake(pp, now, r.get("only_ride", False), len(rs))   # stake_rule.py: Kelly x75 on the blend, x2 only ride, x1.5 field<=8, max 5u
                BETS.append((race, r["horse"], now, ours, stake, bool(a), early))
                tags.append(("<span class='tag edge'>EDGE</span>" if a else "<span class='tag val'>value</span>") + f"<span class='tag'>stake {stake:.1f}u = ${100 * stake:,.0f}</span>")
            if early: tags.append("<span class='tag early'>early only</span>")
        th = T[i]; order = np.argsort(th); ups = [(tnames[j], th[j]) for j in order[::-1][:3] if th[j] > 0.08]; dns = [(tnames[j], th[j]) for j in order[:3] if th[j] < -0.08]
        why = " · ".join([f"<span class='up'>{t} {pct(c)}</span>" for t, c in ups] + [f"<span class='dn'>{t} {pct(c)}</span>" for t, c in dns]) or "nothing stands out either way"
        why = why.rstrip()
        if ours > 15 and not fuv and not isfs: fuv_note = "our price over $15 (outside the backtested band)"
        else: fuv_note = ""
        reason = (f"<b>No bet:</b> {fuv_note}. " if fuv_note else "") + (f"<b>{'No bet' if (fuv and not early) else 'Early only' if early else ''}:</b> {html.escape(fuv.replace('EARLY: ', ''))}. " if fuv else "") + (f"<b>No bet:</b> first starter. " if isfs else "")
        H.append(f"<div class='r'><div class='px'>${ours:,.2f}</div><div><span class='nm'>{html.escape(r['horse'])}</span>{''.join(tags)}<span class='mk'> · now {'$%.2f' % now if now else 'no price'} · take at ${ours * (1 + THR):,.2f} or better</span></div>"
                 f"<div class='why'>{reason}<b>Why:</b> {why}.<br>{html.escape(' · '.join(facts(i, race)))}{(' · <b>angles:</b> ' + html.escape('; '.join(a))) if a else ''}</div></div>")
# ---- top of the page: race bar (sticky) and the bets, inserted after the title ----------------------------------
NAV_CSS = ("<style>.nav{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:#fff;display:flex;gap:6px;overflow-x:auto;"
           "padding:8px 0;margin:0 0 12px;border-bottom:1px solid #e3e3e3;-webkit-overflow-scrolling:touch}.nav a{flex:0 0 auto;min-width:44px;"
           "text-align:center;padding:9px 10px;border-radius:6px;background:#f0f0f0;color:#1b1b1b;text-decoration:none;font-weight:600;font-size:14px}"
           ".nav a.hb{background:#1b5e20;color:#fff}h2{scroll-margin-top:64px}.bets{border:2px solid #1b5e20;border-radius:8px;padding:12px 14px;margin:0 0 18px}"
           ".bets h2{margin:0 0 8px;border:0;padding:0;font-size:17px}.bets table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}"
           ".bets td,.bets th{padding:6px 6px;border-bottom:1px solid #e3e3e3;text-align:right}.bets td:nth-child(2),.bets th:nth-child(2),.bets td:first-child,.bets th:first-child{text-align:left}"
           ".bets th{font-size:12px;color:#555;font-weight:600}.tw{overflow-x:auto}.bets .note{font-size:12.5px;color:#555;margin-top:8px}"
           "@media(prefers-color-scheme:dark){.nav{background:#121212;border-color:#333}.nav a{background:#2a2a2a;color:#eee}.nav a.hb{background:#2e7d32}"
           ".bets td,.bets th{border-color:#333}.bets th,.bets .note{color:#aaa}}</style>")
races_with_bets = {b_[0] for b_ in BETS}
HB, EDGE_T, EARLY_T = " class='hb'", " <span class='tag edge'>EDGE</span>", " <span class='tag early'>early only</span>"
nav = "<nav class='nav'><a href='#bets' class='hb'>Bets</a>" + "".join(f"<a href='#r{rc}'{HB if rc in races_with_bets else ''}>R{rc}</a>" for rc in sorted(races)) + "</nav>"
top = [NAV_CSS, nav, "<div class='bets' id='bets'>"]
if taken_md:
    try:
        tl = []
        for l in open(taken_md):   # the FIRST table only
            if l.strip().startswith("|"): tl.append(l.strip())
            elif tl: break
        if len(tl) >= 2:
            hdr = [c.strip() for c in tl[0].strip("|").split("|")]
            body = [[c.strip() for c in l.strip("|").split("|")] for l in tl[2:]]
            top.append("<h2>Bets taken</h2><div class='tw'><table><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in hdr) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in body) + "</table></div><div style='height:14px'></div>")
    except OSError:
        pass
if BETS:
    top.append(f"<h2>Bets at these prices ({len(BETS)})</h2><div class='tw'><table><tr><th>Race</th><th>Horse</th><th>Price</th><th>Ours</th><th>Stake</th><th>Take at</th></tr>"
               + "".join(f"<tr><td><a href='#r{rc}'>R{rc}</a></td><td>{html.escape(h)}{EDGE_T if ed else ''}{EARLY_T if ea else ''}</td>"
                         f"<td>${n_:,.2f}</td><td>${o_:,.2f}</td><td>{st:.1f}u</td><td>${o_ * (1 + THR):,.2f}+</td></tr>" for rc, h, n_, o_, st, ed, ea in BETS)
               + "</table></div><div class='note'>Take a bet only at or above its take-at price. Stakes: x2 when it is the jockey's only ride at the meeting, x1.5 in a field of 8 or fewer, most 5u; $100 a unit.</div>")
else:
    top.append("<h2>Bets at these prices</h2><div class='note'>None: no runner is 20% or more over our price within the rules. Where there is no market yet, each race below shows our price and the take-at price.</div>")
top.append("</div>")
H[1:1] = top
open(out, "w").write("\n".join(H)); print("ok", out)
