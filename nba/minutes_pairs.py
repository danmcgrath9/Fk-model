"""Who absorbs a missing teammate's minutes, pair by pair.

For player p and rotation teammate j (same team, same season), from EARLIER games only:
p's average minutes in games j missed, minus p's average minutes in games j played.
Tonight, summed over the rotation teammates who are missing:
  pair_min_delta   sum of those differences (only pairs with 2+ games each way)
  pair_n           how many missing teammates had enough history to count
  pair_starts_delta  the same for p starting (share of games started)
"Missing" = played in one of the team's last 3 games with a 15+ minute average, not tonight.
That is the pros' approach to injuries (redistribute to the specific teammates who take the
minutes) rather than our existing team-level "vacated minutes".

Tested like model_v2: walk-forward, all prop-able player-games, gain in average miss with a
95% bootstrap range by game. Here absences are the actual ones (who did not play); the 7pm
injury-report version comes after, if this shows enough.

    python nba/minutes_pairs.py
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

import model_v2 as m2
import project as pr
from features import DATA, FEATURES_MIN, FEATURES_RATE

NEW = ["pair_min_delta", "pair_n", "pair_starts_delta"]


def pair_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["date", "gameId"])
    out = []
    for (team, season), g in df.groupby(["teamId", "season"], sort=False):
        games = g.drop_duplicates("gameId")[["gameId", "date"]].sort_values(["date", "gameId"]).gameId.tolist()
        by_game = {gid: x for gid, x in g.groupby("gameId")}
        # running sums: (p, j) -> [min sum when j out, n, min sum when j in, n, starts out, starts in]
        acc = defaultdict(lambda: [0.0, 0, 0.0, 0, 0.0, 0.0])
        post = {}        # p -> latest min_ewm5_post
        recent = []      # the last 3 games' player sets
        for gid in games:
            x = by_game[gid]
            tonight = dict(zip(x.personId, x["min"]))
            starts = dict(zip(x.personId, x.starter.astype(float)))
            seen = set().union(*recent) if recent else set()
            missing = [j for j in seen if j not in tonight and post.get(j, 0) >= 15]
            for p in tonight:
                d, n, ds = 0.0, 0, 0.0
                for j in missing:
                    a = acc[(p, j)]
                    if a[1] >= 2 and a[3] >= 2:
                        d += a[0] / a[1] - a[2] / a[3]
                        ds += a[4] / a[1] - a[5] / a[3]
                        n += 1
                out.append((gid, p, d if n else np.nan, n, ds if n else np.nan))
            # update with tonight (after the features for tonight were taken)
            rota = [j for j in seen | set(tonight) if post.get(j, 0) >= 15]
            for p, mins in tonight.items():
                for j in rota:
                    if j == p:
                        continue
                    a = acc[(p, j)]
                    if j in tonight:
                        a[2] += mins; a[3] += 1; a[5] += starts[p]
                    else:
                        a[0] += mins; a[1] += 1; a[4] += starts[p]
            post.update(dict(zip(x.personId, x.min_ewm5_post)))
            recent = (recent + [set(tonight)])[-3:]
    return pd.DataFrame(out, columns=["gameId", "personId", *NEW])


def main() -> None:
    df = pd.read_parquet(DATA / "features.parquet")
    df = df[df.game_ok & df.min_ewm5.notna()]
    df = df.merge(pair_features(df), on=["gameId", "personId"], how="left")
    rng = np.random.default_rng(0)
    for season in pr.TEST:
        train = df[(df.season < season) & (df.season >= pr.TRAIN[0])]
        test = df[df.season == season]
        a = m2.predict(m2.fit(train, FEATURES_MIN, FEATURES_RATE), test, FEATURES_MIN, FEATURES_RATE)
        b = m2.predict(m2.fit(train, FEATURES_MIN + NEW, FEATURES_RATE + NEW), test,
                       FEATURES_MIN + NEW, FEATURES_RATE + NEW)
        keep = pr.propable(test)
        parts = []
        for name, mask in [("all", keep), ("teammate out", keep & (test.pair_n.fillna(0) > 0))]:
            for st in ["min", "pts"]:
                c = "min_proj" if st == "min" else f"{st}_proj"
                ea, eb = (a.loc[mask, c] - test.loc[mask, st]).abs(), (b.loc[mask, c] - test.loc[mask, st]).abs()
                gg = pd.DataFrame({"g": test.loc[mask, "gameId"], "d": ea - eb}).groupby("g").d.agg(["sum", "size"])
                s, n = gg["sum"].to_numpy(), gg["size"].to_numpy()
                i = rng.integers(0, len(gg), (1000, len(gg)))
                bt = s[i].sum(1) / n[i].sum(1)
                parts.append(f"{name} {st} {ea.mean():.3f}->{eb.mean():.3f} "
                             f"[{np.percentile(bt, 2.5):+.3f},{np.percentile(bt, 97.5):+.3f}] (n={int(mask.sum())})")
        print(season, " | ".join(parts))


if __name__ == "__main__":
    main()
