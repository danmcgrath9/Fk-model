"""A small made-up league in the shape of the Cricsheet tables, for tests that must run without the data."""
import numpy as np
import pandas as pd

TEAMS = ['Heat', 'Sixers', 'Stars', 'Scorchers']


def league(n_matches=30, seed=1, balls=60):
    rng = np.random.default_rng(seed)
    squads = {t: [f'{t}_{k}' for k in range(13)] for t in TEAMS}
    m, pl, dl, inn = [], [], [], []
    day = pd.Timestamp('2023-12-01')
    for i in range(n_matches):
        mid = f'm{i:03d}'
        a, b = rng.choice(TEAMS, 2, replace=False)
        xi = {t: list(rng.choice(squads[t], 11, replace=False)) for t in (a, b)}
        first = a if rng.random() < 0.5 else b
        order = [first, b if first == a else a]
        totals = {}
        for n, team in enumerate(order, start=1):
            bowl_team = order[1 - (n - 1)]
            bats, nxt = xi[team], 2
            striker, non = bats[0], bats[1]
            runs = wkts = legal = 0
            for k in range(balls):
                if wkts >= 10:
                    break
                bowler = xi[bowl_team][6 + (k // 6) % 5]
                wide = rng.random() < 0.04
                r = 0 if wide else int(rng.choice([0, 1, 2, 4, 6], p=[0.4, 0.35, 0.1, 0.1, 0.05]))
                out = (not wide) and rng.random() < 0.05
                dl.append(dict(match_id=mid, innings=n, team=team, super_over=False, over=k // 6, seq=k % 6 + 1,
                               batter=striker, non_striker=non, bowler=bowler, runs_batter=r, runs_extras=int(wide),
                               runs_total=r + int(wide), non_boundary=False, legal=not wide, wides=int(wide), noballs=0,
                               byes=0, legbyes=0, penalty=0, n_wickets=int(out), player_out=striker if out else None,
                               wicket_kind='caught' if out else None, fielders=xi[bowl_team][0] if out else None,
                               player_out_2=None, wicket_kind_2=None))
                runs += r + int(wide)
                legal += not wide
                if out:
                    wkts += 1
                    striker = bats[nxt] if nxt < 11 else striker
                    nxt += 1
                elif r % 2 == 1:
                    striker, non = non, striker
            inn.append(dict(match_id=mid, innings=n, team=team, super_over=False, runs=runs, wickets=wkts, legal_balls=legal))
            totals[team] = runs
        winner = max(totals, key=totals.get) if totals[a] != totals[b] else None
        m.append(dict(match_id=mid, competition='Big Bash League', season='2023/24' if i < n_matches // 2 else '2024/25',
                      start_date=(day + pd.Timedelta(days=2 * i)).strftime('%Y-%m-%d'), gender='male',
                      team1=a, team2=b, venue=['Gabba', 'Adelaide Oval'][i % 2], toss_winner=a, toss_decision='bat',
                      bat_first=first, winner=winner, result='win' if winner else 'tie', method=None))
        for t in (a, b):
            pl += [dict(match_id=mid, team=t, list_order=k + 1, player=p, player_id='id_' + p) for k, p in enumerate(xi[t])]
    return pd.DataFrame(m), pd.DataFrame(pl), pd.DataFrame(dl), pd.DataFrame(inn)
