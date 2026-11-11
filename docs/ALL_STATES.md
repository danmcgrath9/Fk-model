# All states: one model, trained on every state (built 11 Nov 2026, dormant until the archive)

Founder, 11 Nov 2026: "I want the training for other states as well ... I want the same model", "I'm buying the
history ... that history saves us doing a full pull", and "we want to do a pull every morning of all states". Order
agreed the same night: nothing is pulled for the other states until the national archive is in and an all-states
model has been tested; then the daily pull is switched on.

## What the archive is (Form King #api Slack, Oct 2026)
National, 5 benchmarked runs a runner (the depth our race forms carry, so the model's inputs are the same), from
1 Jul 2025 to the day before Dave produces it: about 2,980 meetings, 23,000 races, 284,000 runners over 15 months,
NZ and HK excluded. That is about 4.6 times Victoria's racing (VIC: 318 races and 40 meetings a month). Dave cleaned
and froze the data from 1 Jul 2025 for point-in-time use (lws and exp pre-race safe; Betfair SP gaps fixed); an API
1.1.1 regeneration was planned for late October, and an `asAt` parameter was under discussion.

## Built, and safe for Victoria
| piece | what it does | Victoria today |
|---|---|---|
| `fk/states.py` | a state list as Form King writes it (`VIC,NSW`); `ALL` = the 8 Australian states | "VIC" means what it did |
| `fk/history.py`, `fk/db.py` | the race readers take a state list | same rows for "VIC" |
| `scripts/export_dataset.py` | `--state` list, `--history` several folders, a `state` array per race | checked 11 Nov: the new code's Victorian export matches the 10 Nov dataset race for race and value for value (one race's going differs, filled from horses the gap fill added) |
| `scripts/archive_to_history.py` | archive -> history day files, other states only by default, into `history_states` | Victoria's `history` release untouched |
| `fk archive` workflow | uploads `history_states` to its own release, `history-states` | |
| `fk export` workflow | `state` and `branch` inputs (defaults VIC, datasets) | unchanged by default |
| `fk retrain` workflow | `state` input; anything but VIC saves to `challenger-allstates`, never live | the nightly run is VIC |
| `research/form_gbm/t_allstates.py` | the test (below) | |
| `fk all states` workflow | the other states' morning pull and next-morning results, run by hand only | no schedule |
| `scripts/history_pull.py --count-only`, `fk state count` | prices a range at 1 credit a day before paying | |

## When the archive arrives
1. Put the zip on Google Drive, shared as anyone-with-the-link. Run **fk archive** with its file id, the password
   (typed into the workflow form, never into chat), script `archive_to_history.py`. It writes and uploads the other
   states' day files. (If the national zip is too big for one runner, it can be run a few states at a time with
   `--states`.)
2. **fk export** with state `ALL`, branch `datasets-allstates`: the all-states training set.
3. `t_allstates.py DS_VIC.npz DS_ALL.npz A`, then `B`. Four ways: Victoria only (today), one model on all states, the
   same told the state, and a separate model for each state trained on that state alone (founder: "different
   states might have different rules"). Scored on Victorian races none of them saw, in both halves, and on every
   other state, so each state can end up with whichever wins there. Betting rules are scored with Victoria's open
   rule everywhere; each state's own betting rules are set from its own results, on paper first.
4. Goes live only if the all-states model is closer to Betfair SP on Victoria in both halves, and on the founder's
   word. Then the nightly retrain runs with state ALL, the live pricer's history becomes the all-states dataset, and
   the daily pull for the other states is switched on.

## Before the daily all-states pull is switched on
- Credits: one pull a race (2), speedmaps (5 a meeting), the list (1 a day) and results (5 a meeting) for the other
  states is about 5,000 a month on the archive's volumes, inside the 30,000 with Victoria (October: 11,943). No
  first-time profiles outside Victoria: the model is a 5-run model and the race form carries every runner's 5
  benchmarked runs and whole career; profiles only feed the form pages.
- Database: it is 1.24 GB and race cards are most of it (9,103 runner rows, 308 MB). The other states would add about
  20 MB a day, so old races have to move to the history files on a schedule (scripts/db_to_history.py, fk db to
  history: copy, verify from a fresh download, then delete). That schedule is a founder decision; it is not on.
- Pricing time: the live pricer fits its network part on the whole history at price time (price_day3.py), so a
  history 4.6 times larger makes each meeting slower to price. Measure it on the first all-states price run.
- Gap: the archive ends the day before it is produced, so the sooner the daily pull starts after it, the smaller the
  gap. A gap is filled with fk backtest (state input) at about 2 credits a race.
