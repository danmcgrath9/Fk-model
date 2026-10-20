"""Pull historical prop lines from DunkAPI for the players in a request file.

Runs from the `nba props pull` GitHub workflow (the cloud box cannot reach DunkAPI), with
the key in the DUNKAPI_API_KEY secret. Never prints the key.

Credit rules, because the free key is 500 a month:
* a hard cap per run (`max_credits` in the request file, and never below a 20-credit floor
  of what DunkAPI says is left);
* idempotent: a player-market already saved under nba/lines/dunkapi/ is skipped, so a
  re-run only buys what is missing;
* every call's credits used and remaining are written to nba/lines/dunkapi/ledger.csv.

What DunkAPI's own docs say the data is (read before trusting it): one row per game with
the closing line (median across books, or one book's), and an "opening" line that for
the NBA is usually the SAME number, because the archive mostly holds one pre-game
capture per line. So this measures us against roughly the close, not the open.

    python nba/pull_dunkapi.py nba/requests/dunkapi_first_pull.json
"""
from __future__ import annotations

import csv
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "lines" / "dunkapi"
COST_SEARCH = 1          # DunkAPI client docs, v0.1.4
COST_HISTORY = 10
FLOOR = 20               # never spend the account below this (a request may set "floor")
PAUSE = 3.0              # seconds between calls: DunkAPI rate-limited a back-to-back run


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum() or ch == " ").strip()


def pick_player(results: list[dict], wanted: str) -> dict | None:
    """Exact (accent-blind) full-name match only. Anything else is refused, not guessed."""
    w = norm(wanted)
    for p in results:
        name = p.get("name") or p.get("full_name") or p.get("display_name") or ""
        if norm(name) == w:
            return p
    return None


class Budget:
    def __init__(self, cap: int, floor: int = FLOOR):
        self.cap, self.floor, self.spent, self.remaining = cap, floor, 0, None

    def can(self, cost: int) -> bool:
        if self.spent + cost > self.cap:
            return False
        return self.remaining is None or self.remaining - cost >= self.floor

    def record(self, client, what: str, ledger: Path, expected: int) -> None:
        # If DunkAPI sends no counter, count the documented price rather than zero.
        used = client.last_credits_used if client.last_credits_used is not None else expected
        self.spent += used
        self.remaining = client.last_credits_remaining
        new = not ledger.exists()
        with ledger.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["utc", "call", "credits_used", "credits_remaining"])
            w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), what, used, self.remaining])


def main(request_path: str) -> int:
    import time

    from dunkapi import APIError, Client, InsufficientCreditsError, RateLimitError

    if not os.environ.get("DUNKAPI_API_KEY"):
        # Not an error: the workflow fires on the first push, before the secret exists.
        print("SKIPPED: DUNKAPI_API_KEY is not set (add it as a GitHub secret). Nothing pulled, no credits spent.")
        return 0
    req = json.loads(Path(request_path).read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = OUT / "ledger.csv"
    ids_path = OUT / "players.json"
    ids = json.loads(ids_path.read_text()) if ids_path.exists() else {}
    client = Client()
    budget = Budget(int(req["max_credits"]), int(req.get("floor", FLOOR)))
    problems = []

    for p in req["players"]:
        key = str(p["personId"])
        if key not in ids:
            if not budget.can(COST_SEARCH):
                problems.append(f"budget: stopped before searching {p['name']}")
                break
            time.sleep(PAUSE)
            try:
                res = client.search_players(p["name"], limit=5)
            except RateLimitError:
                problems.append(f"rate limited before searching {p['name']}; re-run to continue")
                break
            budget.record(client, f"search_players {p['name']}", ledger, COST_SEARCH)
            hit = pick_player(res.get("players", []), p["name"])
            if hit is None:
                problems.append(f"no exact name match for {p['name']}: "
                                f"{[x.get('name') for x in res.get('players', [])]}")
                continue
            ids[key] = {"name": p["name"], "dunkapi_id": str(hit.get("player_id") or hit.get("id"))}
            ids_path.write_text(json.dumps(ids, indent=1))
        did = ids[key]["dunkapi_id"]
        for market in req["markets"]:
            dest = OUT / f"{key}_{market}.json"
            if dest.exists():
                continue
            if not budget.can(COST_HISTORY):
                problems.append(f"budget: stopped before {p['name']} {market}")
                break
            time.sleep(PAUSE)
            try:
                data = client.get_prop_history(did, market, from_date=req["from_date"],
                                               to_date=req["to_date"], limit=200)
            except RateLimitError:
                problems.append(f"rate limited at {p['name']} {market}; re-run to continue")
                break
            except InsufficientCreditsError:
                problems.append("DunkAPI says the account is out of credits")
                break
            except APIError as exc:
                problems.append(f"{p['name']} {market}: HTTP {exc.status_code} {exc.message}")
                continue
            budget.record(client, f"get_prop_history {p['name']} {market}", ledger, COST_HISTORY)
            dest.write_text(json.dumps({"personId": p["personId"], "name": p["name"],
                                        "dunkapi_id": did, "market": market, "data": data}, indent=1))
            rows = data.get("games") or data.get("rows") or data.get("history") or []
            more = data.get("next_from_date")
            print(f"{p['name']:<16} {market:<16} {len(rows):>4} games"
                  + (f"  (more from {more}, not pulled)" if more else ""))

    print(f"\nCredits spent this run: {budget.spent}; DunkAPI says remaining: {budget.remaining}")
    for line in problems:
        print("PROBLEM:", line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "nba/requests/dunkapi_first_pull.json"))
