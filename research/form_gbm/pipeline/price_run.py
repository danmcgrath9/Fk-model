"""The whole pricing run for new Victorian meetings, start to sheets, in one command (12 Nov 2026, founder: "Are you
fucking kidding, the run takes an hour? Thats way to fkn long").

    python3.13 price_run.py [--dates D,D] [--no-pull] [--force --track TRACK] [--all] [--inputs-run RUN_ID] [--replace]

1. One GitHub run (fk price run): the pulls, every input script for every new meeting, and one export per date.
2. Fetch its files (the `pricing` branch), cut each meeting out of its date's export, apply the form adjustments.
3. Price every meeting side by side (pricemtg.sh, the same steps as by hand), with its header worked out here: going
   (Soft for 15mm+ rain in the 3 days before, otherwise the official rating), PROVISIONAL when a runner has no rider,
   PAPER ONLY when the model has no race at the track since its 3 Jun holdout began.
4. Races already open (fluc) come off the pre-open sheet and are listed as missed with what they opened at; write
   -betmatic-preopen.csv and -all.csv (a meeting that already has one is left alone unless --replace), put the
   open-bets box on each page, rebuild each day page, commit, and print the summary the founder message is built from.
Publishing the artifacts and sending to BetMatic stay with the session (they are tool calls).

--inputs-run RUN_ID reuses a price run already on the pricing branch (no dispatch). --all prices meetings that
already have a sheet too (a test); with --replace their sheets are rewritten."""
from __future__ import annotations

import argparse, collections, concurrent.futures as cf, csv, datetime as dt, io, json, os, re, subprocess, sys, time
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

S = Path(__file__).resolve().parent
FK = Path("/home/user/fk-model"); L = FK / "data" / "live_bets"; R = FK / "research" / "form_gbm"
API = "https://api.github.com/repos/danmcgrath9/Fk-model"
MEL = ZoneInfo("Australia/Melbourne")
HOLDOUT = "2026-06-03"
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def gh(path, data=None):
    req = urllib.request.Request(API + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Accept": "application/vnd.github+json", "Content-Type": "application/json"},
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        return json.loads(body) if body else {}


def log(msg):
    print(f"[{dt.datetime.now(MEL):%H:%M:%S}] {msg}", flush=True)


def dispatch_and_wait(inputs) -> str:
    t0 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)
    gh("/actions/workflows/fk-price-run.yml/dispatches", {"ref": "main", "inputs": inputs})
    log(f"fk price run dispatched {inputs}")
    run = None
    while True:
        time.sleep(10)
        if run is None:
            for x in gh("/actions/workflows/fk-price-run.yml/runs?per_page=5")["workflow_runs"]:
                if dt.datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) >= t0:
                    run = x["id"]; log(f"run {run}"); break
            continue
        # The pricing files are pushed before the form reports are built, so stop waiting as soon as the branch
        # carries this run (the reports can take minutes and the pricing does not need them).
        subprocess.run(["git", "-C", str(FK), "fetch", "-q", "origin", "pricing"], check=False)
        rid = subprocess.run(["git", "-C", str(FK), "show", "origin/pricing:RUN_ID"], capture_output=True, text=True).stdout.strip()
        if rid == str(run):
            log("pricing files are up"); return str(run)
        r = gh(f"/actions/runs/{run}")
        if r["status"] == "completed":
            sys.exit(f"STOP: fk price run {run} {r['conclusion']} without pushing its pricing files")


def fetch(run_id: str) -> Path:
    """The pricing branch for this run. The reports step runs after the push, so the branch is there before the run
    finishes; poll until RUN_ID matches."""
    out = S / "run" / run_id
    for _ in range(60):
        subprocess.run(["git", "-C", str(FK), "fetch", "-q", "origin", "pricing"], check=False)
        rid = subprocess.run(["git", "-C", str(FK), "show", "origin/pricing:RUN_ID"], capture_output=True, text=True).stdout.strip()
        if rid == run_id:
            out.mkdir(parents=True, exist_ok=True)
            subprocess.run(f"git -C {FK} archive origin/pricing | tar -x -C {out}", shell=True, check=True)
            return out
        time.sleep(10)
    sys.exit(f"STOP: the pricing branch never showed run {run_id}")


def fluc_rows(path: Path):
    s = path.read_text() if path.exists() else ""
    a = s.find("CSV-BEGIN"); b = s.find("CSV-END")
    if a < 0:
        return []
    return list(csv.DictReader(io.StringIO(s[a + 9:(b if b > 0 else len(s))].strip())))


def rain_before(path: Path, race_day: str):
    """mm of rain on the three days before race day (actual or forecast), and race day itself."""
    if not path.exists():
        return None, None
    d = dt.date.fromisoformat(race_day); before = {str(d - dt.timedelta(days=k)) for k in (1, 2, 3)}
    tot = day = 0.0; seen = False
    for m in re.finditer(r"\| (\d{4}-\d{2}-\d{2})(?: \(forecast\))? \| ([\d.]+) \|", path.read_text()):
        seen = True
        if m.group(1) in before: tot += float(m.group(2))
        if m.group(1) == race_day: day = float(m.group(2))
    return (round(tot, 1), round(day, 1)) if seen else (None, None)


def model_history():
    import numpy as np
    z = np.load(S / "model" / "ds" / "model_ds.npz", allow_pickle=True)
    t = np.asarray(z["track"]).astype(str); d = np.asarray(z["date"]).astype(str)
    return collections.Counter(x for x, y in zip(t, d) if y >= HOLDOUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", default=""); ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--track", default="")
    ap.add_argument("--all", action="store_true"); ap.add_argument("--inputs-run"); ap.add_argument("--replace", action="store_true")
    ap.add_argument("--only", default="", help="meeting ids, comma separated")
    ap.add_argument("--test", action="store_true", help="files under <prefix>-test, no commit (a timing test on meetings already priced)")
    a = ap.parse_args()
    t_start = time.time()
    if a.inputs_run:
        run_id = a.inputs_run
    else:
        run_id = dispatch_and_wait({"dates": a.dates, "pull": "no" if a.no_pull else "yes", "force": "yes" if a.force else "no",
                                    "track": a.track, "all": "yes" if a.all else "no"})
    W = fetch(run_id); log(f"inputs in {W}")
    idx = list(csv.DictReader(open(W / "index.tsv"), delimiter="\t"))
    new = [m for m in idx if m["new"] == "1" and int(m["races"]) > 0 and (not a.only or m["meeting_id"] in a.only.split(","))]
    if a.test:
        for m in idx: m["prefix"] += "-test"
    if not new:
        log("no new meeting"); print("SUMMARY: no new meeting"); return
    import numpy as np
    hist = model_history()
    now = dt.datetime.now(MEL); G = "r" + now.strftime("%m%d%H%M")
    jobs, info = [], {}
    for m in new:
        mid, d, P = m["meeting_id"], m["date"], m["prefix"]; md = W / mid
        fl = fluc_rows(md / "fluc.md")
        ids = sorted({r["race_id"] for r in fl})
        if not ids:
            log(f"STOP {mid}: no race ids in its fluc output"); continue
        up = W / f"upcoming-{d}.npz"
        cut = W / f"{mid}.npz"; adj = W / f"{mid}-adj.npz"
        subprocess.run([sys.executable, str(S / "cut_meeting.py"), str(up), str(cut), ",".join(ids)], check=True)
        fa = subprocess.run([sys.executable, str(R / "form_adjust_npz.py"), str(cut), str(adj)], capture_output=True, text=True, cwd=R)
        adj_note = " ".join(l for l in fa.stdout.splitlines() if "not in this export" not in l).strip()
        z = np.load(adj, allow_pickle=True)
        tracks = sorted(set(map(str, z["track"]))); track = m["track"]
        # riders: a runner with no rider that is not an emergency (entry numbers: race|number|name|emergency|scratched)
        em = {}
        for l in (md / "entry_numbers.md").read_text().splitlines():
            p = l.split("|")
            if len(p) == 5 and p[0].isdigit():
                em[(int(p[0]), norm(p[2]))] = (p[3] == "True" or p[4] == "True")
        rn = z["race_number"][z["race_idx"]]
        no_rider = sum(1 for j, nm, r_ in zip(z["jockey"].astype(str), z["name"].astype(str), rn)
                       if not j.strip() and not em.get((int(r_), norm(nm)), False))
        rain, rday = rain_before(md / "forecast.md", d)
        hist_n = sum(hist[t] for t in tracks)
        paper = hist_n == 0
        going_word = "Soft (15mm+ rain)" if (rain or 0) >= 15 else "official going"
        opened = sorted({int(r["race"]) for r in fl if r.get("open") or r.get("race_open_ms")})
        dow = dt.date.fromisoformat(d).strftime("%a %-d %b")
        flags = []
        if not opened: flags.append("no market yet")
        else: flags.append(f"market open in R{','.join(map(str, opened))}")
        if no_rider: flags.append(f"PROVISIONAL: {no_rider} runners without a rider")
        if paper: flags.append("PAPER ONLY (no race at this track since the 3 Jun holdout)")
        head = f"# {track} {dow}, {going_word}, final fields; " + "; ".join(flags)
        name = track.split(" ")[0] if track.startswith("Sandown") else track
        title = f"{name} {dow}" + (" (paper)" if paper else " (provisional)" if no_rider else "")
        info[mid] = dict(m=m, P=P, paper=paper, no_rider=no_rider, rain=rain, rday=rday, opened=opened, fl=fl,
                         head=head, title=title, name=name, adj=adj_note, soft=(rain or 0) >= 15, hist=hist_n)
        if (rain or 0) >= 15:
            log(f"{mid}: {rain}mm in the 3 days before: needs a Soft export (fk-export going) before pricing; NOT priced here")
            continue
        jobs.append((mid, P, adj, md / "scratchings.md", md / "entry_numbers.md", head, title))
    # the model folder's scripts once
    subprocess.run(f"cd {S}/model && for f in {R}/*.py; do cp -u \"$f\" . ; done; "
                   f"cmp -s {R}/pipeline/F9_names_live.txt F9_names.txt || cp {R}/pipeline/F9_names_live.txt F9_names.txt", shell=True)
    t_model = time.time(); res = []
    # A. each meeting: entry numbers, prices file (mkprices), scratched runners dropped (drop_scr) -> model/<TAG>-scr.npz
    ready = []
    for mid, P, npz, scr, nums, head, title in jobs:
        TAG = P.replace("-", ""); SN = S / "model" / f"{TAG}-scr.npz"
        subprocess.run(["cp", str(nums), str(L / f"{P}-entry-numbers.txt")], check=True)
        mk = subprocess.run([sys.executable, str(S / "mkprices.py"), str(scr), str(nums), str(L / f"{P}-prices.txt"), head],
                            capture_output=True, text=True)
        ds = subprocess.run([sys.executable, "drop_scr.py", str(npz), str(L / f"{P}-prices.txt"), str(SN)], cwd=S / "model",
                            capture_output=True, text=True)
        if mk.returncode or ds.returncode:
            log(f"STOP {mid}: {(mk.stdout + mk.stderr + ds.stdout + ds.stderr)[-300:]}"); res.append((mid, False, 0, W / f"{mid}-price.log")); continue
        info[mid]["mk"] = mk.stdout.strip(); ready.append((mid, P, npz, scr, nums, head, title, SN))
    # B. ONE price_day3 for every meeting: its networks train on the whole history (about 3 minutes), so once a run
    if ready:
        Z = [dict(np.load(r[7], allow_pickle=True)) for r in ready]
        comb, off = {}, 0
        for z in Z:
            nrun, nrace = len(z["race_idx"]), len(z["race_id"])
            for k, v in z.items():
                if k in ("cols", "past_fields", "sec_fields") or v.ndim == 0 or v.shape[:1] not in ((nrun,), (nrace,)):
                    comb.setdefault(k, v); continue
                comb.setdefault(k, []).append(v + off if k == "race_idx" else v)
            off += nrace
        for k, v in list(comb.items()):
            if isinstance(v, list): comb[k] = np.concatenate(v)
        CS = S / "model" / f"run-{G}-scr.npz"; CJ = S / "model" / f"run-{G}-v5s1.json"
        np.savez(CS, **comb)
        log(f"one model run for {len(ready)} meetings ({int(comb['race_idx'].max()) + 1} races, {len(comb['race_idx'])} runners)")
        pdr = subprocess.run([sys.executable, "price_day3.py", str(CS), str(CJ)], cwd=S / "model", capture_output=True, text=True)
        log(f"model run done in {round(time.time() - t_model)}s: {pdr.stdout.strip().splitlines()[-1] if pdr.stdout.strip() else ''}")
        if pdr.returncode:
            sys.exit(f"STOP: price_day3 {pdr.stdout[-400:]} {pdr.stderr[-400:]}")
        allrows = json.load(open(CJ))
        for mid, P, npz, scr, nums, head, title, SN in ready:
            ids = set(map(str, np.load(SN, allow_pickle=True)["race_id"]))
            mine = [r for r in allrows if r["race_id"] in ids]
            json.dump(mine, open(L / f"{P}-{G}-v5s1.json", "w"), indent=1)
    # C. the rest of each meeting (stage 2, blend, angles, sheet, orders, take-at: about 20 seconds each), side by side
    def finish(r):
        mid, P, npz, scr, nums, head, title, SN = r
        t = time.time(); lg = W / f"{mid}-price.log"
        with open(lg, "w") as fh:
            rc = subprocess.run(["bash", str(S / "pricemtg.sh"), P, G, str(npz), str(scr), str(nums), head, title],
                                stdout=fh, stderr=subprocess.STDOUT, cwd=S, env=dict(os.environ, V5S1_DONE="1")).returncode
        ok = (L / f"{P}-{G}-orders.csv").exists() and "meeting done" in lg.read_text()
        return mid, ok, round(time.time() - t), lg
    with cf.ThreadPoolExecutor(max_workers=max(1, len(ready))) as ex:
        res += list(ex.map(finish, ready))
    for mid, ok, secs, lg in res:
        log(f"{mid}: {'ok' if ok else 'FAILED, see ' + str(lg)} in {secs}s")
    out = [f"# Price run {run_id}, tag {G}, {round((time.time() - t_start) / 60, 1)} minutes"]
    for mid, ok, secs, lg in res:
        I = info[mid]; P = I["P"]
        if not ok:
            out.append(f"\n## {I['title']}: PRICING FAILED ({lg})"); continue
        rows = list(csv.DictReader(open(L / f"{P}-{G}-orders.csv")))
        allrows = list(csv.DictReader(open(L / f"{P}-{G}-orders-all.csv")))
        opened = {str(r) for r in I["opened"]}
        openp = {(r["race"], norm(r["name"])): r.get("open") for r in I["fl"] if r.get("open")}
        missed = collections.defaultdict(list)
        for r in rows:
            if r["race"] in opened:
                o = openp.get((r["race"], norm(r["horse"])))
                fill = o and float(o) >= float(r["min_odds"]) and float(o) <= float(r["max_odds"])
                missed[(r["race"], r["horse"], r["our_price"], o)].append(float(r["stake_units"]) if fill else 0.0)
        exists = (L / f"{P}-betmatic-preopen.csv").exists()
        if exists and not a.replace:
            out.append(f"\n## {I['title']}: already has a pre-open sheet, left alone (priced as {G} for comparison)")
            continue
        for src, dst in ((rows, f"{P}-betmatic-preopen.csv"), (allrows, f"{P}-betmatic-preopen-all.csv")):
            keep = [r for r in src if r["race"] not in opened]
            with open(L / dst, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(src[0].keys()) if src else ["race"]); w.writeheader(); w.writerows(keep)
        page = S / "pages" / f"{P.replace('-', '')}-market.html"
        subprocess.run([sys.executable, "betmatic_html.py", str(L / f"{P}-betmatic-preopen.csv"), P, str(page)], cwd=R,
                       capture_output=True)
        H = collections.OrderedDict()
        for r in (x for x in rows if x["race"] not in opened):
            k = (int(r["race"]), r["number"], r["horse"]); h = H.setdefault(k, {"our": float(r["our_price"]), "min": 9e9, "most": 0.0})
            h["min"] = min(h["min"], float(r["min_odds"])); h["most"] = max(h["most"], float(r["total_if_all_fire"].rstrip("u")))
        blank = sum(1 for r in rows if not r["number"].strip())
        out.append(f"\n## {I['title']}: {len(H)} horses, up to {sum(h['most'] for h in H.values()):.2f}u"
                   f"{'' if not blank else f', {blank} ORDERS WITHOUT A NUMBER'}")
        out.append(f"{I['head'][2:]}. Rain {I['rain']}mm in the 3 days before, {I['rday']}mm on the day. "
                   f"Model races here since the holdout: {I['hist']}." + (f" Form adjustments: {I['adj']}" if I['adj'] else ""))
        out.append(f"page {page}")
        out.append("| Race | # | Horse | Ours | Min | Most |\n|---|---|---|---|---|---|")
        for (rc, n, nm), h in sorted(H.items(), key=lambda kv: (kv[0][0], -kv[1]['most'])):
            out.append(f"| R{rc} | {n} | {nm} | ${h['our']:.2f} | ${h['min']:.2f} | {h['most']:.2f}u |")
        for (rc, nm, our, o), st in sorted(missed.items()):
            out.append(f"MISSED R{rc} {nm}: opened ${float(o):.2f} against ours ${float(our):.2f}" + (f", would have filled {sum(st):.2f}u" if sum(st) else ", under its minimum") if o else f"MISSED R{rc} {nm}: no open price")
        # THE SAME BETS AFTER A MISSED OPEN (founder, 12 Nov 2026: "clearly we stick with same", "I also LOVE the two
        # hours, can get on like every bookmaker"; night/t_minutes.py: the bets that were value at the open, struck at
        # the price now, beat a sheet placed late at every minute to 2 hours, +59% at the open to +24% at 2 hours).
        # Each horse whose orders would have filled at the open is backed for that stake at any price now, while the
        # race is within 2 hours of its open: -late.csv, sent with when=best (best price across every bookmaker session).
        ropen = {}
        for r in I["fl"]:
            if r.get("race_open_ms"): ropen[r["race"]] = float(r["race_open_ms"])
        now_ms = time.time() * 1000; late = []
        for (rc, nm, our, o), st in sorted(missed.items()):
            if o and sum(st) > 0 and rc in ropen and now_ms - ropen[rc] <= 2 * 3600e3:
                r0 = next(r for r in rows if r["race"] == rc and r["horse"] == nm)
                late.append(dict(r0, min_odds="1.01", max_odds="1000.00", stake_units=f"{sum(st):.2f}",
                                 stake_dollars=f"{sum(st) * 50:.0f}", order="1 of 1", total_if_all_fire=f"{sum(st):.2f}u",
                                 note=f"late: the same bet as at the open (${float(o):.2f}), struck at the best price now, "
                                      f"{round((now_ms - ropen[rc]) / 60e3)} min after the open"))
        if late:
            with open(L / f"{P}-late.csv", "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(late[0].keys())); w.writeheader(); w.writerows(late)
            out.append(f"LATE SHEET {L / f'{P}-late.csv'}: " + "; ".join(f"R{x['race']} {x['horse']} {x['stake_units']}u" for x in late)
                       + " (send now with when=best)")
    # day pages: every meeting of each date that has a page in the scratch folder
    times = W / "race_times_all.md"
    with open(times, "w") as fh:
        for f in sorted(W.glob("*/race_times.md")): fh.write(f.read_text() + "\n")
        for f in sorted(S.glob("times_*.md")): fh.write(f.read_text() + "\n")
    for d in sorted({info[mid]["m"]["date"] for mid in info}):
        parts, names = [], []
        for m in (x for x in idx if x["date"] == d and (not a.test or x["prefix"].endswith("-test"))):
            P = m["prefix"]; page = S / "pages" / f"{P.replace('-', '')}-market.html"
            if not page.exists() or not (L / f"{P}-betmatic-preopen.csv").exists():
                continue
            if m["meeting_id"] in info:
                nm = info[m["meeting_id"]]["title"].replace(" " + dt.date.fromisoformat(d).strftime("%a %-d %b"), "")
            else:
                hd = (L / f"{P}-prices.txt").read_text().split("\n")[0] if (L / f"{P}-prices.txt").exists() else ""
                base = m["track"].split(" ")[0] if m["track"].startswith("Sandown") else m["track"]
                nm = base + (" (paper)" if "PAPER" in hd else " (provisional)" if "PROVISIONAL" in hd else "")
            names.append(nm); parts.append(f"{nm}={page}@{times}")
        out_page = S / "pages" / f"{d.replace('-', '')}-day{'-test' if a.test else ''}.html"   # a test never touches the real day page
        ttl = f"{dt.date.fromisoformat(d).strftime('%A %-d %b')}: {', '.join(names)}"
        subprocess.run([sys.executable, "day_page.py", str(out_page), ttl, *parts], cwd=R, capture_output=True)
        out.append(f"\nDAY PAGE {d}: {out_page} ({ttl})")
    if not a.test:
        msg = (f"Price run {run_id} (tag {G}): {', '.join(info[m]['title'] for m in info)}\n\n"
               "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
               "Claude-Session: https://claude.ai/code/session_01EWqEfn1skQfDPb65tQpKTS")
        subprocess.run(["bash", "-c", f"(flock 9; cd {FK} && git add data/live_bets && git commit -q -F - && "
                        "git pull -q --rebase origin main && git push -q origin main) 9>/tmp/fkgit.lock"], input=msg, text=True)
    out.append(f"\nDone in {round((time.time() - t_start) / 60, 1)} minutes.")
    (W / "summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
