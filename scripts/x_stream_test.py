"""Can X tell us within seconds that an account has posted? (18 Nov 2026; founder: "can we confirm if he tweets, you
know in 2 second"). A TEST: it reads, it bets nothing. Two ways are checked with the app's own token:
  1. THE STREAM: one rule (from:USERNAME, no retweets, no replies) and a connection held for 25 seconds. A 200 with
     keep-alives means X will push each new post down the wire as it is made.
  2. POLLING: one timeline check, printing the rate-limit headers, which say how often the check may be made.
    python scripts/x_stream_test.py USERNAME [--since POST_ID]
The token is X_BEARER_TOKEN and is never printed."""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument("user"); ap.add_argument("--since"); ap.add_argument("--hold", type=int, default=25); a = ap.parse_args()
tok = (os.environ.get("X_BEARER_TOKEN") or "").strip()
if not tok: sys.exit("NO TOKEN: X_BEARER_TOKEN is not set")
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
clean = lambda s: s.replace(tok, "<TOKEN>")[:400]


def call(method, path, body=None, timeout=30):
    req = urllib.request.Request("https://api.x.com/2" + path, data=json.dumps(body).encode() if body is not None else None, headers=H, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


# 2. polling: how often may the timeline be checked?
st = json.load(open(f"data/x-watch/{a.user}.json")) if os.path.exists(f"data/x-watch/{a.user}.json") else {}
if st.get("id"):
    q = dict(exclude="replies,retweets", max_results=5, **({"since_id": a.since or st.get("since")} if (a.since or st.get("since")) else {}))
    t0 = time.time(); c, h, b = call("GET", f"/users/{st['id']}/tweets?" + urllib.parse.urlencode(q)); dt = time.time() - t0
    rl = {k.lower(): v for k, v in h.items() if k.lower().startswith("x-rate-limit")}
    print(f"POLL: status {c} in {dt:.2f}s; posts returned {len((json.loads(b).get('data') or [])) if c == 200 else '-'}; rate limit {rl or 'no headers'}")
    if c != 200: print("  ", clean(b))
# 1. the stream
c, h, b = call("GET", "/tweets/search/stream/rules")
print(f"STREAM RULES read: status {c}"); rules = (json.loads(b).get("data") or []) if c == 200 else []
if c != 200: print("  ", clean(b))
want = f"from:{a.user} -is:retweet -is:reply"
if c == 200 and not any(r.get("value") == want for r in rules):
    c2, _, b2 = call("POST", "/tweets/search/stream/rules", {"add": [{"value": want, "tag": f"tips {a.user}"}]})
    print(f"STREAM RULE add: status {c2}; {clean(b2)}")
elif c == 200:
    print("STREAM RULE already there:", want)
req = urllib.request.Request("https://api.x.com/2/tweets/search/stream?tweet.fields=created_at&expansions=attachments.media_keys&media.fields=url,type", headers=H)
t0 = time.time(); got = 0; beats = 0
try:
    with urllib.request.urlopen(req, timeout=a.hold + 10) as r:
        print(f"STREAM connect: status {r.status} in {time.time() - t0:.2f}s; held for {a.hold}s")
        while time.time() - t0 < a.hold:
            line = r.readline()
            if not line: break
            if line.strip(): got += 1; print("  POST on the stream:", clean(line.decode("utf-8", "replace"))[:200])
            else: beats += 1
    print(f"STREAM: {got} posts, {beats} keep-alives in {time.time() - t0:.0f}s: the connection holds" if (got or beats) else "STREAM: connected, nothing came down in the hold (no keep-alive yet)")
except urllib.error.HTTPError as e:
    print(f"STREAM connect: status {e.code}; {clean(e.read().decode('utf-8', 'replace'))}")
except Exception as e:
    print(f"STREAM: connected {time.time() - t0:.0f}s then {type(e).__name__} (a read timeout with no post is normal): keep-alives {beats}, posts {got}")
