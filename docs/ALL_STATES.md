# All states: one model per state, never mixed (built 11 Nov 2026, dormant until the archive)

**Founder decision, 11 Nov 2026: "they're all separate and train on their own states ... because different states
might have different rules", then "can't mix the states up".** Every state gets its own model, trained only on its
own races, with its inputs built over its own races only, the way the Victorian model already is. Victoria's model is
unchanged. No model is ever trained on more than one state, and each state's betting rules are set from its own
results, on paper first. (The pooled arms in t_allstates.py were written before this decision and are a record
only; fk retrain refuses a state list.)

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
| `fk retrain` workflow | `state` input, ONE state only (a list or ALL is refused); another state saves to `challenger-STATE`, never live | the nightly run is VIC |
| `research/form_gbm/t_ownstate.py` | the test: each state's own model on its own races (below) | Victoria is the reference row |
| `fk all states` workflow | the other states' morning pull and next-morning results, run by hand only | no schedule |
| `scripts/history_pull.py --count-only`, `fk state count` | prices a range at 1 credit a day before paying | |

## When the archive arrives
1. Put the zip on Google Drive, shared as anyone-with-the-link. Run **fk archive** with its file id, the password
   (typed into the workflow form, never into chat), script `archive_to_history.py`. It writes and uploads the other
   states' day files. (If the national zip is too big for one runner, it can be run a few states at a time with
   `--states`.)
2. **fk export** with state `ALL`, branch `datasets-allstates`: every state's races in one file, used only as a
   container; t_ownstate.py cuts each state out on its own before anything is built.
3. `t_ownstate.py DS_ALL.npz A`, then `B`: each state's own model, trained before the fold's cut on its own races and
   scored on its own races after it, with Victoria as the reference row. A state with fewer than 300 training races
   is named and gets no model yet. Profit is Victoria's open rule everywhere, as a common yardstick only.
4. A state is priced (on paper first) only on the founder's word, with its own model, its own history dataset for
   the pricer, and its own betting rules from its own results. Then the daily pull for the other states is switched
   on. Victoria carries on exactly as it is.

## Before the daily all-states pull is switched on
- Credits: one pull a race (2), speedmaps (5 a meeting), the list (1 a day) and results (5 a meeting) for the other
  states is about 5,000 a month on the archive's volumes, inside the 30,000 with Victoria (October: 11,943). No
  first-time profiles outside Victoria: the model is a 5-run model and the race form carries every runner's 5
  benchmarked runs and whole career; profiles only feed the form pages.
- Database: it is 1.24 GB and race cards are most of it (9,103 runner rows, 308 MB). The other states would add about
  20 MB a day, so old races have to move to the history files on a schedule (scripts/db_to_history.py, fk db to
  history: copy, verify from a fresh download, then delete). That schedule is a founder decision; it is not on.
- Pricing time: the live pricer fits its network part on the state's history at price time (price_day3.py), so a
  state's meetings price in about the time its history size says (NSW and QLD near Victoria's, the small states
  faster). Measure it on each state's first price run.
- Gap: the archive ends the day before it is produced, so the sooner the daily pull starts after it, the smaller the
  gap. A gap is filled with fk backtest (state input) at about 2 credits a race.
