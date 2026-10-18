"""The live stake, one definition.

From 18 Oct 2026 (founder: "surely there can be max bets without stupid rules, can we test everything?" then "Yep do
it"): plain Kelly x125 on the blend sqrt(ours x market), everything x5/8, capped at 5u. No only-ride or small-field
multipliers: the size comes from the edge alone, so a max bet is any bet with enough edge. t_stakes.py, holdout from
3 Jun: +935u, +33.6% at the open, worst drawdown 68u, 103 bets of 4.5u+ (the old rule: +711u, +35.6%, 62u, 15).

Before 18 Oct (8 Oct to 18 Oct): Kelly x75 capped at 4u, x2 when the jockey's only ride, x1.5 when the field is 8 or
fewer, never over 8u, then x5/8 (git history; t_batch.py to t_batch3.py)."""
KELLY, SCALE, MAX_UNITS = 125, 5 / 8, 5.0


def stake(pp: float, price: float, only_ride: bool = False, field: int = 0) -> float:
    """Units to stake at `price` for a runner with blended chance `pp`. only_ride and field are accepted so every caller
    keeps working, and no longer change the stake (18 Oct 2026)."""
    if price <= 1:
        return 0.0
    k = max(0.0, ((pp * price) ** 0.5 - 1) / (price - 1))
    return round(min(MAX_UNITS, KELLY * k * SCALE), 2)
