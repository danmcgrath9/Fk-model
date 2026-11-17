"""One read from the X API with the app's Bearer Token, to prove the token and the credits work (18 Nov 2026).
    python scripts/x_read_test.py [POST_ID]
Reads ONE public post (half a cent on pay-per-use). Token from X_BEARER_TOKEN; never printed."""
import json, os, sys, urllib.error, urllib.request
tok = (os.environ.get("X_BEARER_TOKEN") or "").strip()
if not tok:
    sys.exit("NO TOKEN: the secret X_BEARER_TOKEN is not set in the twitter environment")
pid = sys.argv[1] if len(sys.argv) > 1 else "2122457608963395586"
req = urllib.request.Request(f"https://api.x.com/2/tweets/{pid}?tweet.fields=created_at,author_id", headers={"Authorization": f"Bearer {tok}"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read()); h = r.headers
        t = (d.get("data") or {})
        print(f"OK {r.status}: post {t.get('id')} by author {t.get('author_id')} at {t.get('created_at')}: {str(t.get('text'))[:100]!r}")
        print("rate limit:", h.get("x-rate-limit-remaining"), "of", h.get("x-rate-limit-limit"), "left in this window")
        if d.get("errors"): print("errors:", json.dumps(d["errors"])[:300])
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", "replace").replace(tok, "<TOKEN>")[:500]
    print(f"FAILED {e.code}: {body}"); sys.exit(1)
