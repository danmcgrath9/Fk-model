"""Benter's second stage, tested on what we hold (26 Oct 2026, founder: "Are we doing a Benter style model?").

    python research/harness/hx_stage2.py DIR LABEL      (after hx_model.py, which writes DIR/hx_preds.parquet)

Benter (1994): stage 1 is a fundamental model; stage 2 fits log p = a*log(model) + b*log(market) per race, renormalised,
so the market's price and the model's price are weighed by data. The weight on the model says whether it knows anything
the market does not. Our live market price will be the OPEN (recorder); until enough opens exist, the pre-play WAP
stands in: it is a market price from before the off, softer than BSP, like the open. Fitted on the validation months
(Jul-Dec 2024), scored on the holdout (2025-26) in two halves, against WAP alone and BSP."""
import os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_model import winner_ll, kl_to_bsp
from hx_data import renorm


def combo(df, a, b):
    return renorm(np.exp(a * np.log(df.p_model) + b * np.log(df.p_wap)), df.race)


def main(d, label):
    df = pd.read_parquet(os.path.join(d, "hx_preds.parquet"))
    df = df[df.p_wap.notna() & df.p_wap.notna().groupby(df.race).transform("all")]
    va, ho = df[df.half == "validation"], df[df.half != "validation"]
    grid = [(a, b) for a in np.arange(0, 1.01, 0.05) for b in np.arange(0.5, 1.51, 0.05)]
    a, b = min(grid, key=lambda ab: winner_ll(combo(va, *ab), va.won, va.race))
    print(f"# {label}: Benter stage 2 (model + pre-play WAP)\n")
    print(f"fitted on validation ({va.race.nunique():,} races): log p = {a:.2f} x log(model) + {b:.2f} x log(WAP)\n")
    print("| price | LL 1st half | LL 2nd half | KL to BSP 1st half | KL 2nd half |\n|---|---|---|---|---|")
    for name, f in (("model alone", lambda x: x.p_model), ("pre-play WAP alone", lambda x: x.p_wap),
                    ("stage 2: model + WAP", lambda x: combo(x, a, b)), ("BSP", lambda x: x.p_bsp)):
        r = []
        for h in ("first half", "second half"):
            s = ho[ho.half == h]
            p = np.asarray(f(s))
            r += [winner_ll(p, s.won, s.race), kl_to_bsp(p, s.p_bsp, s.race)]
        print(f"| {name} | {r[0]:.4f} | {r[2]:.4f} | {r[1]:.4f} | {r[3]:.4f} |")
    print("\nA weight on the model above zero that improves on WAP alone in both halves means the model knows something "
          "the pre-play market does not.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "harness")
