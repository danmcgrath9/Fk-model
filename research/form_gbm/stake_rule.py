"""The live stake, one definition (8 Oct 2026, t_batch.py to t_batch4.py; founder: 'max is 5u, so make an 8u 5u').

Kelly x75 on the blend sqrt(ours x market), capped at 4u; x2 when it is the jockey's only ride at the meeting; x1.5
when the field is 8 or fewer (x3 for both); never over 8u; then everything x5/8, so the biggest bet is 5u and a
normal capped bet is 2.5u. Backtest (holdout / before): open +69.1% / +56.8%, worst drawdown $4,346 / $7,669 at
$100 a unit, against the 4u plan's +65.7% / +51.9% and $5,282 / $9,772."""
ONLY_RIDE, SMALL_FIELD, SMALL_FIELD_MAX, CEILING, SCALE = 2.0, 1.5, 8, 8.0, 5 / 8


def stake(pp: float, price: float, only_ride: bool, field: int) -> float:
    if price <= 1:
        return 0.0
    base = min(4.0, 75 * max(0.0, ((pp * price) ** 0.5 - 1) / (price - 1)))
    s = base * (ONLY_RIDE if only_ride else 1.0) * (SMALL_FIELD if field <= SMALL_FIELD_MAX else 1.0)
    return round(min(s, CEILING) * SCALE, 2)
