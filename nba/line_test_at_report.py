"""The line test again, with projections that only know the injury report at each hour.

Same 12 players and DunkAPI lines as line_test.py / probability.py, but the projection is
the one at_report.py made from the official injury report filed by that time (US Eastern),
not one that knew who actually played. The 2025/26 blend is fitted on 2024/25 only, as
before. DunkAPI's capture time is not published, so every snapshot is shown.

    python nba/line_test_at_report.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import line_test as lt
import probability as pb
from features import DATA


def score(j: pd.DataFrame, var) -> dict:
    o, u = pb.p_over_under(np.maximum(j.proj.to_numpy(), 0.05), j.line.to_numpy(),
                           np.stack([var[s] for s in j.st]))
    j = j.assign(p_model=o / (o + u))
    io, iu = 1 / j.dec_over, 1 / j.dec_under
    j["p_mkt"] = io / (io + iu)
    j = j[j.result != "push"].copy()
    j["went_over"] = (j.result == "over").astype(float)
    tr, te = j[j.date < "2025-07-01"], j[j.date >= "2025-07-01"]
    w = pb.fit_blend(tr)
    side = np.where(j.proj > j.line, "over", "under")
    dec = np.where(side == "over", j.dec_over, j.dec_under)
    pnl = np.where(j.result == side, dec - 1, -1.0)
    big = (j.proj - j.line).abs() >= 2
    y = te.went_over.to_numpy()
    return {"lines": len(j),
            "our miss": (j.proj - j.actual).abs().mean(),
            "line miss": (j.line - j.actual).abs().mean(),
            "our side ROI": pnl.mean(),
            "2+ apart: bets": int(big.sum()), "2+ apart: ROI": pnl[big].mean(),
            "25/26 log loss blend": pb.log_loss(pb.blend(te, w), y),
            "25/26 log loss market": pb.log_loss(te.p_mkt.to_numpy(), y),
            "model weight": w[1]}


def main() -> None:
    lines = lt.load_lines()
    lines = lines[lines.over_odds.notna() & lines.under_odds.notna() & lines.actual.notna()].copy()
    lines["dec_over"] = lt.american_to_decimal(lines.over_odds)
    lines["dec_under"] = lt.american_to_decimal(lines.under_odds)
    var = pb.fit_alphas()
    a = pd.read_parquet(DATA / "projections_at_report.parquet")
    a["date"] = pd.to_datetime(a.date).dt.strftime("%Y-%m-%d")
    after = pd.read_parquet(DATA / "projections.parquet")
    after["date"] = pd.to_datetime(after.date).dt.strftime("%Y-%m-%d")
    after["snapshot"] = "knew who played"
    rows = {}
    for snap, g in pd.concat([a, after]).groupby("snapshot", sort=False):
        long = pd.concat([g[["date", "personId", f"{st}_proj"]].rename(columns={f"{st}_proj": "proj"}).assign(st=st)
                          for st in ["pts", "reb", "ast", "fg3m"]])
        j = lines.merge(long, on=["personId", "date", "st"], how="inner")
        rows[snap] = score(j, var)
    t = pd.DataFrame(rows).T
    pd.set_option("display.width", 200)
    print(t.to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
