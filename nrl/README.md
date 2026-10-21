# NRL: team markets and player props (started 21 Oct 2026)

Prices NRL head-to-head, line and total, and player props (anytime try scorer first), the house way
(`prompts/HOUSE_STANDARD.md` on `afl-props`): our own probability for every outcome, bet only when the
book's price beats ours by enough. Separate from racing and the other sports: everything lives in
`nrl/` and the `nrl-*` workflows, with its own data release (`nrl-history`). No Form King key, no
BetMatic orders. Paper only until the founder says otherwise.

## Where it stands

| Step | What | Status |
|---|---|---|
| 1. Inventory | every source, what it holds, terms, cost | in progress: see `docs/INVENTORY.md` |
| Data | uselessnrlstats (RLP, cleaned): every game and player-game 1998 to round 17 2026 | mirrored: 5,744 games, 194,905 player-games |
| Data | Champion Data match-centre stats (run metres, tackles) via nrlR's endpoints | terms and a 3-request sample: `nrl sources` workflow |
| Odds | The Odds API | capped probe (300 credits): `nrl lines` workflow |
| 2-7 | data layer, team model, props, backtest, team-news test, paper season | not started |

## Running it

```
pip install -r nrl/requirements.txt
python nrl/data/mirror.py --out nrl/cache          # or: gh release download nrl-history --dir nrl/cache
```

The `nrl sources` workflow identifies itself by User-Agent; set the repository variable `NRL_CONTACT`
(Settings > Secrets and variables > Actions > Variables) to add a contact to it.
