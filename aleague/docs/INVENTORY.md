# Step 1: data inventory (21 Oct 2026)

From the `aleague data` run of 21 Oct 2026 (raw responses: `inventory_v1.tar.gz` on the
`aleague-history` release). One look per source, 8 s apart.

| Source | What came back | Terms | Usable? |
|---|---|---|---|
| The Odds API | not yet: the `ODDS_API_KEY` secret is not set in Fk-model, so the probe stopped at 0 credits | paid, ours | yes, once the secret is added |
| football-data.co.uk | no A-League file: `/new/AUS.csv` does not exist (its extra leagues are ARG, AUT, BRA, CHN, DNK, FIN, IRL, JPN, MEX, NOR, POL, ROU, RUS, SWE, SWZ, USA) | n/a | no |
| FBref | 403 on every page from GitHub's runners | terms forbid automated access without written permission; Opta advanced stats (xG) withdrawn Jan 2026 | no |
| ESPN public JSON | the best data seen: per-player goals, assists, shots, shots on target, cards, fouls, starter, subbed in/out (minutes from substitution times), team shots/possession/corners, attendance, venue; games back to 2012 | Disney terms forbid copying or extracting by "robot, spider, script, or other automated means" | no, under the house rule |
| FotMob | not sampled | "use of automatic services (robots, crawler...) ... not permitted" | no |
| Sofascore | 403 | terms page 403 | no |
| Transfermarkt | not sampled | terms page did not load | no (known to forbid scraping) |
| Ultimate A-League | robots.txt allows match pages | no terms page found | lineups, goals, cards, subs since 2005; no shots. Founder's call |
| API-Football (api-sports.io) | not called: needs an account | licensed API, built for this | best candidate; cost below |
| worldfootballR_data (GitHub) | FBref A-League results mirror, results only, no player stats | MIT mirror | results only |
| Open-Meteo archive | works: hourly temperature, rain, wind | free tier is non-commercial only | founder's call; BOM is the free alternative |

Not found anywhere: a history of named squads and late withdrawals, or of injury lists. ESPN-style
data records who started and who came on, which is "who actually played"; the model will build
from that unless a source turns up.
