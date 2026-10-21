# NRL data inventory (step 1, 21 Oct 2026; pulls done the same day, see the end)

Every figure here comes from a run: the local mirror (`nrl/data/mirror.py`), the `nrl sources`
workflow (robots.txt, terms pages and a 3-request Champion Data sample, kept on the release as
`sources_check.tar.gz`) and the `nrl lines` workflow. Nothing has been bought.

## Stats and results

| Source | What came back | Terms found | Cost |
|---|---|---|---|
| uselessnrlstats (Rugby League Project data, cleaned, on GitHub) | 5,744 games and 194,905 player-games, 1998 to round 17 2026 (last game 28 Jun 2026). Per player: team, jersey, position, tries, goals, field goals, sin bins, send-offs, points. Player points add up to the team score in 99.6% of team-games; every mismatch (28) is in 2026. No minutes, run metres or tackles. Rounds 18-27 and the 2026 finals are missing. | Repo has no licence file; its README invites people to "download, copy or fork". RLP: copyright notice, no terms page (about/terms/copyright all 404); robots.txt blocks only search and custom pages. We read the GitHub copy, never RLP. | free |
| Champion Data match centre (the feed nrlR reads) | Every NRL premiership and finals series 2014-2026 is listed (2026 regular season: 204 games, all complete). Per player per game, about 50 stats: run metres, post-contact metres, tackles, missed tackles, line breaks, tackle breaks, try assists, offloads, kick metres, errors, plus tries and goals. Also per-half splits, team stats, the score flow with the time of every try (so first try scorer can be labelled), and sin bins with times. The sampled game lists 38 players: 34 who played and 4 named reserves with zero involvement. No minutes on field (the interchange list was empty). | No robots.txt on the feed's host; its front page answers 403; Champion Data's company site has `Disallow: /` and no terms page. It is a commercial data company's feed. nrlR (MIT, on CRAN) uses it openly, but nothing grants us a licence. | free; a full pull is about 2,700 requests (one per game, 2014-2026), about 2.5 hours at 3 seconds apart |

## Team lists, late changes, injuries

| Source | What it holds | Terms | Notes |
|---|---|---|---|
| NRL.com team-list articles (Tuesday, plus late mail) | named 22 per club per round, current and archived | download and print "for private, non-commercial use"; no reproduction without consent; robots.txt allows everything | the only route found to "named Tuesday, then withdrew". nrlR parses one article per URL. About 27 articles a season |
| Champion Data extended squad | named reserves who did not take the field (from 2014) | as above | partial: shows who sat out of the final squad, not Tuesday's list |
| Zero Tackle injury list | current injuries and suspensions | no terms page found | current only, no history |

No ready-made history of announced teams or injury lists exists that we found.

## Odds

| Source | Status |
|---|---|
| The Odds API | probe NOT run: the `ODDS_API_KEY` secret is empty in the repo (the AFL probe failed the same way at 01:16 UTC today). 0 credits spent |
| AusSportsBetting historical NRL results and odds (free spreadsheet) | the site refuses GitHub's runners (403) and its robots.txt says `use=reference, ai-train=no` and blocks AI crawlers by name, so we did not fetch it. Reported (not verified) to hold opening and closing head-to-head, line and total prices from about 2009 |

## Weather

| Source | Terms | Cost |
|---|---|---|
| BOM | own content: personal use only, no commercial use, no scraping | free |
| Open-Meteo | free API non-commercial only (CC BY 4.0), 10,000 calls a day; commercial use needs a paid plan | paid plan price is not on the saved page; check before buying |

## What was pulled (21 Oct 2026, founder approved: "do everything you can")

- Champion Data: 2,629 games, 2014 to the 2026 grand final, none missing, one request every 3 seconds.
- NRL.com: 1,105 round team-list and late-mail articles 2009-2026, one request every 3 seconds, for private
  research only. Tuesday's lists survive in the prose articles (2009-2018); from 2020 the archived pages show
  only the match-day 18.
- Correction: RLP's 2026 results stop part-way through round 16 (19 Jun); its later 2026 rows are fixtures
  without results. Champion Data fills 20 Jun to 4 Oct.
