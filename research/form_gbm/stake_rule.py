"""The live stake, one definition.

From 18 Oct 2026 (founder: "surely there can be max bets without stupid rules, can we test everything?" then "Yep do
it"): plain Kelly x125 on the blend sqrt(ours x market), everything x5/8, capped at 5u. No only-ride or small-field
multipliers: the size comes from the edge alone, so a max bet is any bet with enough edge. t_stakes.py, holdout from
3 Jun: +935u, +33.6% at the open, worst drawdown 68u, 103 bets of 4.5u+ (the old rule: +711u, +35.6%, 62u, 15).

From 20 Oct 2026 (founder: "Do our bets get sharper up to 10u", then "fkn love it"): the cap is 10u, was 5u. t_cap.py
on the holdout from 3 Jun with the forecast-BSP blend orders: cap 5u +1,601u (+43.7%), worst drawdown 54u; 7.5u
+1,867u (+45.4%), 64u; 10u +1,989u (+46.0%), 68u; 15u +2,042u, 85u. With the 10u cap ROI rises with stake to the
7.5-10u band (+63%) and the bets at the cap (median open $4.20) make +47%. TAB may not take $500 at an open:
BetMatic's status reports a reduced fill, and the cap comes back down if TAB keeps cutting us.

Before 18 Oct (8 Oct to 18 Oct): Kelly x75 capped at 4u, x2 when the jockey's only ride, x1.5 when the field is 8 or
fewer, never over 8u, then x5/8 (git history; t_batch.py to t_batch3.py)."""
KELLY, SCALE, MAX_UNITS = 125, 5 / 8, 10.0


def stake(pp: float, price: float, only_ride: bool = False, field: int = 0) -> float:
    """Units to stake at `price` for a runner with blended chance `pp`. only_ride and field are accepted so every caller
    keeps working, and no longer change the stake (18 Oct 2026)."""
    if price <= 1:
        return 0.0
    k = max(0.0, ((pp * price) ** 0.5 - 1) / (price - 1))
    return round(min(MAX_UNITS, KELLY * k * SCALE), 2)
