"""Find the shape of Betwatch's beta API (13 Nov 2026: founder has a key for beta.betwatch.com; no public docs).
Reads a few likely addresses, first without the key and then with it in the usual header forms, and prints each one's
status, content type and the first part of the body. The key comes from BETWATCH_BETA_API_KEY and is never printed.
    python scripts/betwatch_beta_probe.py [URL ...]"""
import os, re, sys, urllib.request, urllib.error

KEY = os.environ.get("BETWATCH_BETA_API_KEY", "").strip()
UA = "fk-model/1.0"
URLS = sys.argv[1:] or ["https://beta.betwatch.com/", "https://beta.betwatch.com/docs", "https://beta.betwatch.com/api",
                        "https://beta.betwatch.com/api/docs", "https://beta.betwatch.com/openapi.json",
                        "https://beta.betwatch.com/api/openapi.json", "https://beta.betwatch.com/swagger",
                        "https://api.beta.betwatch.com/", "https://beta-api.betwatch.com/", "https://beta.betwatch.com/graphql",
                        "https://beta.betwatch.com/api/graphql", "https://beta.betwatch.com/llms.txt"]


def fetch(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(4000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read(1500).decode("utf-8", "replace")
    except Exception as e:
        return None, "", f"{type(e).__name__}: {e}"


def clean(s):
    s = s.replace(KEY, "<KEY>") if KEY else s
    return re.sub(r"\s+", " ", s)[:1200]


print(f"key present: {bool(KEY)} (length {len(KEY)})")
for u in URLS:
    st, ct, body = fetch(u, {})
    print(f"\n## {u}\nno key: {st} {ct}\n{clean(body)}")
    links = sorted(set(re.findall(r'(?:href|src)="([^"]*(?:api|doc|swagger|graphql|openapi)[^"]*)"', body, re.I)))
    if links: print("links: " + ", ".join(links[:30]))
    if KEY and st in (401, 403) or (KEY and "graphql" in u):
        for h in ({"X-API-KEY": KEY}, {"Authorization": f"Bearer {KEY}"}, {"x-api-key": KEY, "Content-Type": "application/json"}):
            st2, ct2, b2 = fetch(u, h)
            print(f"with {list(h)[0]}: {st2} {ct2} {clean(b2)[:400]}")
