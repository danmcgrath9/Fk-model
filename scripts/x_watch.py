"""Watch a tipster's X account and read each new tip (18 Nov 2026; founder: "Anthony Don at $50 a unit", "Don't do it
live until I say it"). SHADOW ONLY: it reads, parses and records what it WOULD bet. It places nothing and holds no
BetMatic login. Supersedes the Share-to-Telegram input of betmatic/TIPSTER_BOT_PLAN.md (15 Oct): the X API now reads
the account directly (pay-per-use, half a US cent a post read; a check that finds nothing is free).

    python scripts/x_watch.py USERNAME [--unit 50] [--first 5]

State: data/x-watch/<user>.json (the user id and the last post seen). Log: data/x-watch/<user>.jsonl, one line a post.
New tips print as "TIP ..." lines and are written to data/x-watch/new-tips.md for the workflow to raise as an issue.
His tips are IMAGES (a card: "WARWICK FARM - R1 / CHURCHILLIAN / $3.50 | 5 UNITS WIN"), so each image on a new post is
read by OCR (rapidocr-onnxruntime, installed only when there is an image to read) and parsed; the post's own text is
parsed too. OCR misreads ("R1" as "RI", the bar as "1", no spaces in the track), so a tip is only ever marked
"read", never "verified": the live path must match venue, race and runner to BetMatic's schedule before any bet.
Token from X_BEARER_TOKEN, never printed. His tips are for the founder's own betting; never reposted."""
import datetime, argparse, json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request

ap = argparse.ArgumentParser(); ap.add_argument("user"); ap.add_argument("--unit", type=float, default=50.0)
ap.add_argument("--first", type=int, default=5, help="posts to read on the very first run")
ap.add_argument("--image", help="parse one local image and exit (no X call): a parser check")
ap.add_argument("--from-id", help="re-read the posts after this post id (a test); the place kept is not moved back")
ap.add_argument("--reparse", action="store_true", help="re-read the log's posts with today's parser and print the tips (no X call)")
a = ap.parse_args()
D = "data/x-watch"; os.makedirs(D, exist_ok=True)
STATE, LOG, NEW = f"{D}/{a.user}.json", f"{D}/{a.user}.jsonl", f"{D}/new-tips.md"


def ocr_lines(path):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "rapidocr-onnxruntime"], check=False)
        from rapidocr_onnxruntime import RapidOCR
    res, _ = RapidOCR()(path)
    rows = sorted(((b[0][1], b[0][0], t) for b, t, _ in (res or [])), key=lambda x: (round(x[0] / 12), x[1]))
    return [t.strip() for _, _, t in rows if t.strip()]


# Two shapes, both his (18 Nov 2026). The TIP as he posts it, in text, when he gives it:
#     WARWICK FARM R1 — TODAY / 🏇 CHURCHILLIAN  $3.60 TAB BETR $3.50 Others / 💰 5 Units WIN
# and the recap CARD (an image, posted later): WARWICK FARM - R1 / CHURCHILLIAN / $3.50 | 5 UNITS WIN
RACE = re.compile(r"^([A-Z][A-Z .'&]*?)\s*[-–—]?\s*R(?:ACE)?\s*([0-9IlO|]{1,2})(?:\s*[-–—:]\s*([A-Z].*))?$")
PRICE = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")
UNITS = re.compile(r"(\d+(?:\.\d+)?)\s*UNITS?\b", re.I)
KIND = re.compile(r"\b(EACH\s*WAY|E/W|WIN|PLACE)\b", re.I)
num = lambda s: int(s.replace("I", "1").replace("l", "1").replace("|", "1").replace("O", "0"))
name = lambda h: re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", lambda m: m.group(0).capitalize(), h.strip())
clean = lambda l: re.sub(r"\s+", " ", re.sub(r"^[^A-Za-z0-9$]+", "", l)).strip()          # drop a leading emoji


def parse(lines):
    """Tips from the lines of a post or a card: a TRACK R1 line (in capitals), then the horse, the price(s), the units."""
    tips, i = [], 0
    L = [clean(l) for l in lines]
    while i < len(L):
        m = RACE.match(L[i]) if L[i] == L[i].upper() else None
        if not m or len(m.group(1).strip()) < 3:
            i += 1; continue
        tip = dict(track=m.group(1).strip(), race=num(m.group(2)), when=(m.group(3) or "").strip() or None, horse=None, price=None,
                   prices=[], units=None, kind=None, flags=[])
        j = i + 1
        while j < len(L) and j <= i + 4:
            if L[j] == L[j].upper() and RACE.match(L[j]) and len(RACE.match(L[j]).group(1).strip()) >= 3: break
            ps, u, k = list(PRICE.finditer(L[j])), UNITS.search(L[j]), KIND.search(L[j])
            if ps or u:
                if ps and tip["horse"] is None:
                    h = re.split(r"\s*[-–—]\s*$", L[j][:ps[0].start()].strip())[0].strip()
                    if len(h) >= 3: tip["horse"] = name(h)
                for n_, q in enumerate(ps):                      # each price and the bookmaker named after it, if one is
                    if u is not None and q.start() > u.start(): continue
                    stop = min([x for x in ([ps[n_ + 1].start()] if n_ + 1 < len(ps) else []) + ([u.start()] if u else []) if x > q.end()] or [len(L[j])])
                    lab = " ".join(re.findall(r"[A-Za-z]{2,}", L[j][q.end():stop]))
                    tip["prices"].append([float(q.group(1)), lab])
                if u: tip["units"] = float(u.group(1))
                if k: tip["kind"] = re.sub(r"\s+", " ", k.group(1).upper()).replace("E/W", "EACH WAY")
            elif tip["horse"] is None and len(L[j]) >= 3:
                tip["horse"] = name(L[j])
            if tip["horse"] and tip["prices"] and tip["units"]:
                j += 1; break
            j += 1
        if tip["prices"]: tip["price"] = min(q[0] for q in tip["prices"])          # the price most bookmakers have ("Others")
        if tip["horse"] is None or tip["price"] is None or tip["units"] is None: tip["flags"].append("incomplete")
        if tip["units"] and tip["units"] > 10: tip["flags"].append("units over 10: the bar may have been read as a 1")
        if tip["kind"] is None: tip["flags"].append("no bet type read"); tip["kind"] = "WIN"
        tips.append(tip); i = j
    return tips


def show(t, unit):
    st = f"${t['units'] * unit:,.0f}" if t["units"] else "?"
    px = " / ".join(f"${q[0]:.2f}{' ' + q[1] if q[1] else ''}" for q in t.get("prices") or []) or f"${t['price']}"
    return (f"{t['track']} R{t['race']}{' ' + t['when'] if t.get('when') else ''}: {t['horse']} {px}, {t['units']:g}u {t['kind']} -> would stake {st} at ${t['price']:.2f} or better"
            if not t["flags"] or t["flags"] == ["no bet type read"] else f"{t['track']} R{t['race']} {t['horse']} price {t['price']} units {t['units']} {t['kind']} CHECK: {'; '.join(t['flags'])}")


if a.image:
    ls = ocr_lines(a.image); print("OCR:", ls)
    for t in parse(ls): print("TIP", show(t, a.unit))
    sys.exit(0)

if a.reparse:
    for l in open(LOG):
        d = json.loads(l); tips = parse([x for x in d["text"].split("\n") if x.strip()])
        for o in d.get("ocr") or []: tips += parse(o)
        print(f"post {d['id']} {d['at']}: {len(tips)} tips")
        for t in tips: print("  TIP", show(t, a.unit))
    sys.exit(0)

tok = (os.environ.get("X_BEARER_TOKEN") or "").strip()
if not tok: sys.exit("NO TOKEN: X_BEARER_TOKEN is not set")


def melb_day(iso):
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.fromisoformat((iso or "").replace("Z", "+00:00")).astimezone(ZoneInfo("Australia/Melbourne")).date().isoformat()
    except Exception:
        return (iso or "")[:10]


def x(path, **q):
    req = urllib.request.Request("https://api.x.com/2" + path + ("?" + urllib.parse.urlencode(q) if q else ""), headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"X API {e.code}: {e.read().decode('utf-8', 'replace').replace(tok, '<TOKEN>')[:300]}")


st = json.load(open(STATE)) if os.path.exists(STATE) else {}
if "id" not in st:
    st["id"] = x(f"/users/by/username/{a.user}")["data"]["id"]                      # one user read, once
q = dict(exclude="replies,retweets", expansions="attachments.media_keys", **{"media.fields": "url,type", "tweet.fields": "created_at"})
if a.from_id: q.update(since_id=a.from_id, max_results=20)
elif st.get("since"): q.update(since_id=st["since"], max_results=20)
else: q.update(max_results=max(5, a.first))
d = x(f"/users/{st['id']}/tweets", **q)
media = {m["media_key"]: m for m in (d.get("includes") or {}).get("media", [])}
posts = sorted(d.get("data") or [], key=lambda p: int(p["id"]))
out = []
log = {}
if os.path.exists(LOG):
    for l in open(LOG):
        if l.strip(): r0 = json.loads(l); log[r0["id"]] = r0
for p in posts:
    lines = [l for l in p.get("text", "").split("\n") if l.strip()]; tips = parse(lines); ocr = []
    for k in (p.get("attachments") or {}).get("media_keys", []):
        m = media.get(k) or {}
        if m.get("type") != "photo" or not m.get("url"): continue
        fn = f"/tmp/xw-{p['id']}-{k}.jpg"
        try:
            with urllib.request.urlopen(urllib.request.Request(m["url"], headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r_, open(fn, "wb") as fh:
                fh.write(r_.read())
            ls = ocr_lines(fn); ocr.append(ls); tips += parse(ls)
        except Exception as ex:
            ocr.append([f"OCR FAILED {type(ex).__name__} {getattr(ex, 'code', '')} {m['url'][:60]}"])
    # one tip a runner a day: his recap card repeats the tips he posted in text earlier
    key = lambda t: f"{melb_day(p.get('created_at'))}|{re.sub(r'[^A-Z]', '', t['track'].upper())}|{t['race']}|{re.sub(r'[^A-Z]', '', (t['horse'] or '').upper())}"
    seen = st.setdefault("seen", [])
    for t in tips:
        t["repeat"] = key(t) in seen
        if not t["repeat"] and not t["flags"]: seen.append(key(t))
    st["seen"] = seen[-200:]
    rec = dict(id=p["id"], at=p.get("created_at"), text=p.get("text", ""), ocr=ocr, tips=tips, mode="shadow")
    log[p["id"]] = rec
    print(f"post {p['id']} {p.get('created_at')}: {len(tips)} tips; {p.get('text', '')[:70]!r}")
    tips = [t for t in tips if not t.get("repeat")]
    if tips:
        out.append(f"**{p.get('created_at')}** https://x.com/{a.user}/status/{p['id']}\n" + "\n".join(f"- {show(t, a.unit)}" for t in tips))
        for t in tips: print("TIP", show(t, a.unit))
if posts:
    st["since"] = str(max(int(posts[-1]["id"]), int(st.get("since") or 0)))
    with open(LOG, "w") as fh:
        for k in sorted(log, key=int): fh.write(json.dumps(log[k]) + "\n")
json.dump(st, open(STATE, "w"))
if out:
    open(NEW, "w").write(f"Shadow only: nothing was bet. ${a.unit:g} a unit.\n\n" + "\n\n".join(out) + "\n")
print(f"{len(posts)} new posts, {sum(1 for _ in out)} with tips")
