"""Listen to BetMatic's private WebSocket and append every message to a log, one JSON object per line (14 Oct 2026).
Runs on the founder's always-on machine beside the BetMatic bot. Credentials come from the environment, never from
the repo:  set BETMATIC_EMAIL and BETMATIC_PASSWORD, then  python betmatic_listen.py [LOG.jsonl]
Needs: pip install requests websocket-client rel. WebSocket access must first be enabled by support@betmatic.io.
bet_history fields are not documented yet, so messages are logged raw; the fill parser is written once real
messages exist (see API_NOTES.md)."""
import json, os, sys, time
import requests, websocket, rel

API = "https://betmatic.app"
LOG = sys.argv[1] if len(sys.argv) > 1 else "betmatic-events.jsonl"


def login():
    r = requests.post(f"{API}/api/account/login/", json={"email": os.environ["BETMATIC_EMAIL"],
                                                          "password": os.environ["BETMATIC_PASSWORD"]}, timeout=30)
    r.raise_for_status()
    tok = r.json().get("token")
    if not tok:
        sys.exit("BetMatic login returned no token: check the email and password")
    return tok


def on_message(ws, message):
    try:
        m = json.loads(message)
    except ValueError:
        m = {"category": "unparsed", "raw": message}
    m["_received"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(LOG, "a") as fh:
        fh.write(json.dumps(m) + "\n")
    cat = m.get("category")
    if cat not in ("bet_history", "odds_update_anwser"):
        print("unknown category, logged:", cat)


def main():
    tok = login()
    ws = websocket.WebSocketApp(f"wss://betmatic.app/ws/private?token={tok}", on_message=on_message,
                                on_open=lambda ws: print("connected, logging to", LOG),
                                on_error=lambda ws, e: print("websocket error:", e),
                                on_close=lambda ws, c, m: print("closed:", c, m))
    ws.run_forever(dispatcher=rel, reconnect=5)
    rel.signal(2, rel.abort)
    rel.dispatch()


if __name__ == "__main__":
    main()
