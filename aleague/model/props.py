"""Player-prop pricing for A-League Men: goal scorer, shots, cards.

The machinery is source-agnostic and ready for a player-stats feed; it is NOT yet backed by one. The
data in hand (aleague-history goals.parquet) says who scored and when, but not who played or for how
long, so a per-minute rate cannot be estimated honestly from it: a player with no goal in five matches
may have scored nothing or not played. Projections wait for minutes (docs/INVENTORY.md).

Shape, per the brief: a projection (expected minutes x a per-90 rate, adjusted for the opponent and the
team's expected goals) turned into a count distribution and priced at each line.
  anytime_scorer(team_xg, share, minutes)   P(scores at least once): the player's share of his team's
                                            goals while he is on, scaled by the minutes he plays
  count_over(mean, line, k)                 P(count > line) for a negative binomial with dispersion k
                                            (variance = mean + mean^2 / k; k=None is Poisson)
  shrunk_share(player_goals, team_goals, prior, strength)   a scoring share pulled towards a prior
"""
import math

from scipy.stats import nbinom, poisson


def anytime_scorer(team_xg, share, minutes=90.0):
    """Goals for a player ~ Poisson(team_xg x share x minutes/90), so P(at least one) = 1 - exp(-that)."""
    lam = team_xg * share * min(max(minutes, 0.0), 90.0) / 90.0
    return 1 - math.exp(-lam)


def count_over(mean, line, k=None):
    """P(X > line) for an over/under line such as 1.5 shots."""
    threshold = math.floor(line)  # over 1.5 wins on 2 or more: 1 - P(X <= 1)
    if k is None:
        return float(poisson.sf(threshold, mean))
    p = k / (k + mean)
    return float(nbinom.sf(threshold, k, p))


def shrunk_share(player_goals, team_goals, prior, strength=10.0):
    """(player goals + prior x strength) / (team goals + strength): a few goals move it a little."""
    return (player_goals + prior * strength) / (team_goals + strength)


def fair_price(p):
    return float('inf') if p <= 0 else 1 / p
