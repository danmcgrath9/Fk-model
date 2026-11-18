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
import argparse, json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request

ap = argparse.ArgumentParser(); ap.add_argument("user"); ap.add_argument("--unit", type=float, default=50.0)
ap.add_argument("--first", type=int, default=5, help="posts to read on the very first run")
ap.add_argument("--image", help="parse one local image and exit (no X call): a parser check")
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


RACE = re.compile(r"^([A-Z][A-Z .'&]*?)\s*[-–—]\s*R(?:ACE)?\s*([0-9IlO|]{1,2})$")
PRICE = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")
UNITS = re.compile(r"(\d+(?:\.\d+)?)\s*UNITS?\b", re.I)
KIND = re.compile(r"\b(EACH\s*WAY|E/W|WIN|PLACE)\b", re.I)
num = lambda s: int(s.replace("I", "1").replace("l", "1").replace("|", "1").replace("O", "0"))


def parse(lines):
    """Tips from the lines of a card or a post: a 'TRACK - R1' line, the horse on the next line, then '$3.50 | 5 UNITS WIN'."""
    tips, i = [], 0
    L = [re.sub(r"\s+", " ", l).strip() for l in lines]
    while i < len(L):
        m = RACE.match(L[i].upper())
        if not m:
            i += 1; continue
        tip = dict(track=m.group(1).strip(), race=num(m.group(2)), horse=None, price=None, units=None, kind=None, flags=[])
        j = i + 1
        while j < len(L) and j <= i + 3:
            if RACE.match(L[j].upper()): break
            p, u, k = PRICE.search(L[j]), UNITS.search(L[j]), KIND.search(L[j])
            if p or u:
                if p: tip["price"] = float(p.group(1))
                if u: tip["units"] = float(u.group(1))
                if k: tip["kind"] = re.sub(r"\s+", " ", k.group(1).upper()).replace("E/W", "EACH WAY")
            elif tip["horse"] is None:
                tip["horse"] = L[j].title()
            j += 1
        if tip["horse"] is None or tip["price"] is None or tip["units"] is None: tip["flags"].append("incomplete")
        if tip["units"] and tip["units"] > 10: tip["flags"].append("units over 10: the bar may have been read as a 1")
        if tip["kind"] is None: tip["flags"].append("no bet type read"); tip["kind"] = "WIN"
        tips.append(tip); i = j
    return tips


def show(t, unit):
    st = f"${t['units'] * unit:,.0f}" if t["units"] else "?"
    return (f"{t['track']} R{t['race']} {t['horse']} ${t['price']} {t['units']:g}u {t['kind']} -> would stake {st}"
            if not t["flags"] or t["flags"] == ["no bet type read"] else f"{t['track']} R{t['race']} {t['horse']} price {t['price']} units {t['units']} {t['kind']} CHECK: {'; '.join(t['flags'])}")


if a.image:
    ls = ocr_lines(a.image); print("OCR:", ls)
    for t in parse(ls): print("TIP", show(t, a.unit))
    sys.exit(0)

tok = (os.environ.get("X_BEARER_TOKEN") or "").strip()
if not tok: sys.exit("NO TOKEN: X_BEARER_TOKEN is not set")


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
if st.get("since"): q.update(since_id=st["since"], max_results=20)
else: q.update(max_results=max(5, a.first))
d = x(f"/users/{st['id']}/tweets", **q)
media = {m["media_key"]: m for m in (d.get("includes") or {}).get("media", [])}
posts = sorted(d.get("data") or [], key=lambda p: int(p["id"]))
out = []
for p in posts:
    lines = [l for l in p.get("text", "").split("\n") if l.strip()]; tips = parse(lines); ocr = []
    for k in (p.get("attachments") or {}).get("media_keys", []):
        m = media.get(k) or {}
        if m.get("type") != "photo" or not m.get("url"): continue
        fn = f"/tmp/xw-{p['id']}-{k}.jpg"
        try:
            urllib.request.urlretrieve(m["url"] + "?name=large", fn); ls = ocr_lines(fn); ocr.append(ls); tips += parse(ls)
        except Exception as ex:
            ocr.append([f"OCR FAILED {type(ex).__name__}"])
    rec = dict(id=p["id"], at=p.get("created_at"), text=p.get("text", ""), ocr=ocr, tips=tips, mode="shadow")
    with open(LOG, "a") as fh: fh.write(json.dumps(rec) + "\n")
    print(f"post {p['id']} {p.get('created_at')}: {len(tips)} tips; {p.get('text', '')[:70]!r}")
    if tips:
        out.append(f"**{p.get('created_at')}** https://x.com/{a.user}/status/{p['id']}\n" + "\n".join(f"- {show(t, a.unit)}" for t in tips))
        for t in tips: print("TIP", show(t, a.unit))
if posts: st["since"] = posts[-1]["id"]
json.dump(st, open(STATE, "w"))
if out:
    open(NEW, "w").write(f"Shadow only: nothing was bet. ${a.unit:g} a unit.\n\n" + "\n\n".join(out) + "\n")
print(f"{len(posts)} new posts, {sum(1 for _ in out)} with tips")
