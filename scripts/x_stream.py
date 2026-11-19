"""Hold X's filtered stream open and read each of the tipster's posts the moment it is made (19 Nov 2026; founder:
"WHATS THE POINT OF THE X API IF YOU DON'T AUTOMATICALLY GET CONNECTED"). Replaces the 10-minute check (x_watch.py),
which GitHub ran four times in a day. SHADOW ONLY ("Don't do it live until I say it"): it reads, parses and records what
it WOULD bet; no BetMatic login, no bets.

    python scripts/x_stream.py USERNAME [--unit 50] [--hours 5.8]

The stream rule (from:USERNAME, no retweets, no replies) is added if missing. On a dropped connection it reconnects with
backoff. Each post: the text and any card image (OCR) are parsed with x_watch.py's own parser, the tip is written to
data/x-watch/<user>.jsonl (and the place kept in <user>.json, so the 10-minute check does not read it twice), raised as a
GitHub issue at once (GH_TOKEN), and committed. The token is X_BEARER_TOKEN and is never printed."""
import argparse, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument("user"); ap.add_argument("--unit", type=float, default=50.0)
ap.add_argument("--hours", type=float, default=5.8)
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
# the parser, the OCR and the line format are x_watch.py's, so the two can never disagree
src = open(os.path.join(HERE, "x_watch.py")).read()
ns = {}
exec(src[src.index("import datetime"):src.index("ap = argparse")], ns)
exec(src[src.index("def ocr_lines"):src.index("if a.image:")], ns)
exec(src[src.index("def melb_day"):src.index("def x(path")], ns)
parse, ocr_lines, show, melb_day = ns["parse"], ns["ocr_lines"], ns["show"], ns["melb_day"]
D = "data/x-watch"; os.makedirs(D, exist_ok=True)
STATE, LOG = f"{D}/{a.user}.json", f"{D}/{a.user}.jsonl"
tok = (os.environ.get("X_BEARER_TOKEN") or "").strip()
if not tok: sys.exit("NO TOKEN: X_BEARER_TOKEN is not set")
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
clean = lambda s: s.replace(tok, "<TOKEN>")[:400]
log = lambda *m: print(time.strftime("%H:%M:%S"), *m, flush=True)


def call(method, path, body=None):
    req = urllib.request.Request("https://api.x.com/2" + path, data=json.dumps(body).encode() if body is not None else None, headers=H, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": clean(e.read().decode("utf-8", "replace"))}


want = f"from:{a.user} -is:retweet -is:reply"
c, rules = call("GET", "/tweets/search/stream/rules")
if c == 200 and not any(r.get("value") == want for r in rules.get("data") or []):
    log("rule add", call("POST", "/tweets/search/stream/rules", {"add": [{"value": want, "tag": f"tips {a.user}"}]})[0])
log(f"rule: {want}")


def handle(msg):
    p = msg.get("data") or {}
    if not p.get("id"): return
    media = {m["media_key"]: m for m in (msg.get("includes") or {}).get("media", [])}
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    lines = [l for l in p.get("text", "").split("\n") if l.strip()]; tips = parse(lines); ocr = []
    for k in (p.get("attachments") or {}).get("media_keys", []):
        m = media.get(k) or {}
        if m.get("type") != "photo" or not m.get("url"): continue
        fn = f"/tmp/xs-{p['id']}-{k}.jpg"
        try:
            with urllib.request.urlopen(urllib.request.Request(m["url"], headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r_, open(fn, "wb") as fh:
                fh.write(r_.read())
            ls = ocr_lines(fn); ocr.append(ls); tips += [dict(t, card=True) for t in parse(ls)]
        except Exception as ex:
            ocr.append([f"OCR FAILED {type(ex).__name__}"])
    seen = st.setdefault("seen", [])
    key = lambda t: f"{melb_day(p.get('created_at'))}|{re.sub(r'[^A-Z]', '', t['track'].upper())}|{t['race']}|{re.sub(r'[^A-Z]', '', (t['horse'] or '').upper())}"
    for t in tips:
        t["repeat"] = key(t) in seen or (t.get("card") and any(k_.startswith("|".join(key(t).split("|")[:3]) + "|") for k_ in seen))
        if not t["repeat"] and not t["flags"]: seen.append(key(t))
    st["seen"] = seen[-200:]; st["since"] = str(max(int(p["id"]), int(st.get("since") or 0)))
    json.dump(st, open(STATE, "w"))
    with open(LOG, "a") as fh: fh.write(json.dumps(dict(id=p["id"], at=p.get("created_at"), text=p.get("text", ""), ocr=ocr, tips=tips, mode="shadow-stream")) + "\n")
    new = [t for t in tips if not t.get("repeat")]
    log(f"post {p['id']} {p.get('created_at')}: {len(new)} new tips; {p.get('text', '')[:80]!r}")
    for t in new: log("TIP", show(t, a.unit))
    if new and os.environ.get("GH_TOKEN"):
        body = f"Shadow only: nothing was bet. ${a.unit:g} a unit. Read from the live stream.\n\n**{p.get('created_at')}** https://x.com/{a.user}/status/{p['id']}\n" + "\n".join(f"- {show(t, a.unit)}" for t in new)
        subprocess.run(["gh", "issue", "create", "--title", f"Don tip (shadow): {show(new[0], a.unit)[:80]}", "--body", body], check=False)
    subprocess.run("git add data/x-watch/*.json data/x-watch/*.jsonl && git commit -q -m 'x stream: a post read (shadow)' && "
                   "for i in 1 2 3; do git pull -q --rebase origin main && git push -q origin main && break; sleep 5; done", shell=True, check=False)


q = urllib.parse.urlencode({"tweet.fields": "created_at", "expansions": "attachments.media_keys", "media.fields": "url,type"})
end = time.time() + a.hours * 3600; wait = 5
while time.time() < end:
    try:
        req = urllib.request.Request(f"https://api.x.com/2/tweets/search/stream?{q}", headers=H)
        with urllib.request.urlopen(req, timeout=60) as r:          # X sends a keep-alive every 20 seconds
            log("connected"); wait = 5
            while time.time() < end:
                line = r.readline()
                if not line: raise ConnectionError("stream closed")
                if line.strip():
                    try: handle(json.loads(line))
                    except Exception as ex: log("post not handled:", type(ex).__name__, str(ex)[:200])
    except urllib.error.HTTPError as e:
        body = clean(e.read().decode("utf-8", "replace")); log(f"stream HTTP {e.code}: {body[:200]}")
        wait = 60 if e.code == 429 else min(wait * 2, 300)
    except Exception as ex:
        log("stream dropped:", type(ex).__name__, str(ex)[:120]); wait = min(wait * 2, 120)
    if time.time() < end:
        time.sleep(wait)
log("window over")
