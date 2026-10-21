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
| Ultimate A-League | every match since 2005: line-ups and bench, substitutions with minutes, goals, cards, referee, crowd | **content licensed CC BY 4.0** (site footer); terms (found at /legal/) restrict nothing about access; robots.txt allows /match/ and /matches/; a private API and researcher datasets on request | **yes**: pulled once, 5 s apart (aleague lineups workflow) |
| API-Football (api-sports.io) | not called: needs an account | licensed API, built for this | best candidate; cost below |
| worldfootballR_data (GitHub) | FBref A-League results mirror, results only, no player stats | MIT mirror | results only |
| Open-Meteo archive | works: hourly temperature, rain, wind | free tier is non-commercial only | founder's call; BOM is the free alternative |

Not found anywhere: a history of named squads and late withdrawals, or of injury lists. ESPN-style
data records who started and who came on, which is "who actually played"; the model will build
from that unless a source turns up.

## Second and third looks (21 Oct 2026, inventory2_v1 and inventory3_v1 on the release)

- **Ultimate A-League is the player source.** Its footer licenses the content CC BY 4.0, its terms page
  (Copyright and Trademark section) restricts nothing about access, and robots.txt allows the match
  pages. Each match page has both line-ups with the bench, substitution minutes, a timeline of goals and
  cards with the minute and player, the referee and the crowd: minutes played per player per match,
  which the props need. No shots. The site also runs a private API and offers researchers datasets on
  request (enquiries [at] ultimatealeague.com); asking is the friendlier route for the future and needs
  the founder's OK on the exact email.
- aussportsbetting.com (historical odds spreadsheets): its pages answered 403 to GitHub's runners and its
  terms page could not be read; not used.
