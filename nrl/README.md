# NRL: team markets and player props (started 21 Oct 2026)

Prices NRL head-to-head, line and total, and player props (anytime try scorer first), the house way
(`prompts/HOUSE_STANDARD.md` on `afl-props`): our own probability for every outcome, bet only when the
book's price beats ours by enough. Separate from racing and the other sports: everything lives in
`nrl/` and the `nrl-*` workflows, with its own data release (`nrl-history`). No Form King key, no
BetMatic orders. Paper only until the founder says otherwise.

## Where it stands (21 Oct 2026)

Results: `docs/RESULTS_2026-10-21.md`. Every improvement tried since, and why it was kept or dropped: `docs/RESEARCH_LOG.md`. Sources and terms: `docs/INVENTORY.md`. Everything rebuilds with `bash nrl/build.sh`.

| Step | Status |
|---|---|
| 1. Inventory | done; odds probe built, waits on the ODDS_API_KEY secret |
| 2. Data layer | done: RLP 1998-2026 + Champion Data 2014-2026 joined, Tuesday lists 2009-2018 where they survive; leakage tests pass (team, player, try and props frames) |
| 3. Team model | done: ratings + player ratings; at the open and teams named; final check run once |
| 4. Props | anytime / 2+ / first try scorer; run metres; tackles |
| 5. Backtest | against stand-in lines only (upper bounds); real lines wait for odds |
| 6. Team-news angle | late changes measured (Tuesday list vs who played); book repricing needs recorded prices |
| 7. Paper season | price card ready (h2h, line, total, margin bands, try scorers); price recording from round 1 2027 |
| Since the first results | adopted: key-number margins, travel distance, Champion Data form in the try model. Weather: real in hindsight, not yet shown to survive forecasts |

## Running it

```
pip install -r nrl/requirements.txt
python nrl/data/mirror.py --out nrl/cache          # or: gh release download nrl-history --dir nrl/cache
```

The `nrl sources` workflow identifies itself by User-Agent; set the repository variable `NRL_CONTACT`
(Settings > Secrets and variables > Actions > Variables) to add a contact to it.

Weather data by Open-Meteo.com (CC BY 4.0), free non-commercial API, used for private research.
