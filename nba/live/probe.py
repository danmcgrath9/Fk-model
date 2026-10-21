"""One-off: fetch the NBA's live-data files once and save trimmed samples, so the daily
pipeline is built against the real format. Three requests to cdn.nba.com."""
import json
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "probe"
OUT.mkdir(exist_ok=True)
H = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nba.com/", "Origin": "https://www.nba.com"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
        return json.load(r)


sched = get("https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json")
dates = sched["leagueSchedule"]["gameDates"]
(OUT / "schedule_keys.json").write_text(json.dumps({
    "top": list(sched.keys()), "leagueSchedule": [k for k in sched["leagueSchedule"] if k != "gameDates"],
    "seasonYear": sched["leagueSchedule"].get("seasonYear"), "n_dates": len(dates),
    "first_dates": [d["gameDate"] for d in dates[:3]],
    "first_game": dates[0]["games"][0]}, indent=1))
board = get("https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json")
sb = board["scoreboard"]
(OUT / "scoreboard_sample.json").write_text(json.dumps(
    {"gameDate": sb.get("gameDate"), "n": len(sb.get("games", [])), "first": (sb.get("games") or [None])[0]}, indent=1))
first_reg = next(g["gameId"] for d in dates for g in d["games"] if g["gameId"].startswith("002"))
box = get(f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{first_reg}.json")
g = box["game"]
team = g["homeTeam"]
(OUT / "boxscore_sample.json").write_text(json.dumps({
    "game_keys": list(g.keys()), "team_keys": list(team.keys()),
    "player_example": team["players"][0], "n_players": len(team["players"]),
    "gameId": g["gameId"], "gameStatus": g.get("gameStatus"), "gameTimeUTC": g.get("gameTimeUTC")}, indent=1))
print("ok", first_reg)
