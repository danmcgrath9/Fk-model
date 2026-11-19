"""Who comes across a dog at the start, judged by where dogs get to at the first point, not by their sectional times
(19 Nov 2026, founder, on Warragul race 3: "the 6 crossed it").

Test 96's map (topaz_lines.race_map) counts a dog drawn outside as a crosser only when its early-speed RATING (the
first sectional time) is quicker. Box 6 at Warragul was slower than box 5 on that rating (5th fastest against 4th),
but it had led at the first point in 4 of its last 10 runs against box 5's 3 in 10, and it came across. A dog's
sectional time and where it gets to are not the same thing: a quick beginner out of the boxes can be in front at the
first point on a slower time to the mark.

So the threat here is read from position. Every input is from runs on EARLIER days and today's draw:
  - style_early: the dog's mean place at the first point over its last 10 runs, as a share of the field (0 = led,
    1 = last); style_led_rate: the share of its last 10 runs it led at the first point (both topaz_v2)
  - line_any: its running line, metres from the rail against its box (topaz_lines: tracked where it has 2 or more
    tracked runs, else its run-line code's metres). An unknown line is read as its neighbour's (no wider, no closer)

For each runner (the race's runners in box order):
  cx_out_first    dogs drawn OUTSIDE it that are usually ahead of it at the first point and run no wider than it
                  (by more than topaz_lines.WIDER): they come across it
  cx_out_led      the same, by the share of runs led
  cx_in_first     dogs drawn INSIDE it that are usually ahead of it at the first point and run wider than it (by more
                  than WIDER): they come out across it
  cx_out_pressure the outside crossers' lead over it at the first point (its style_early less theirs), each divided by
                  how many boxes away it is drawn, summed
  cx_nb_out_first its style_early less the nearest dog drawn outside it (positive: that dog is usually ahead of it)
  cx_nb_out_led   the nearest outside dog's led rate less its own
"""
import numpy as np
import pandas as pd

WIDER = 0.5                       # metres, as topaz_lines.WIDER: a dog this much wider (or closer) will cross another
COLS = ["cx_out_first", "cx_out_led", "cx_in_first", "cx_out_pressure", "cx_nb_out_first", "cx_nb_out_led"]


def cross_map(df: pd.DataFrame) -> pd.DataFrame:
    """The crossing inputs for every row of df (columns race_id, box, style_early, style_led_rate, line_any), in df's
    order and index. A runner with no first-point history gets NaN."""
    x = df[["race_id", "box", "style_early", "style_led_rate", "line_any"]].copy()
    x["_i"] = np.arange(len(df))
    x = x.sort_values(["race_id", "box"], kind="mergesort")
    rid = x.race_id.values
    b = x.box.values.astype(float)
    e = x.style_early.values.astype(float)
    led = x.style_led_rate.values.astype(float)
    ln = x.line_any.values.astype(float)
    out = {c: np.full(len(x), np.nan) for c in COLS}
    starts = np.r_[0, np.flatnonzero(rid[1:] != rid[:-1]) + 1, len(x)]
    for a, z in zip(starts[:-1], starts[1:]):
        bb, ee, dd, ll = b[a:z], e[a:z], led[a:z], ln[a:z]
        for j in range(z - a):
            if np.isnan(ee[j]):
                continue
            # an unknown line on either side is read as level with the other: neither wider nor closer
            dl = np.where(np.isnan(ll) | np.isnan(ll[j]), 0.0, ll - ll[j])
            outside, inside = bb > bb[j], bb < bb[j]
            ahead = ee < ee[j]                                        # NaN compares False: no history, no threat
            no_wider, wider = dl <= WIDER, dl > WIDER
            cross_out = outside & ahead & no_wider
            out["cx_out_first"][a + j] = cross_out.sum()
            out["cx_out_led"][a + j] = np.sum(outside & (dd > dd[j]) & no_wider) if np.isfinite(dd[j]) else np.nan
            out["cx_in_first"][a + j] = np.sum(inside & ahead & wider)
            out["cx_out_pressure"][a + j] = np.sum(np.where(cross_out, (ee[j] - ee) / np.maximum(bb - bb[j], 1), 0.0))
            o = np.flatnonzero(outside)
            if len(o):
                k = o[np.argmin(bb[o])]
                out["cx_nb_out_first"][a + j] = ee[j] - ee[k]
                out["cx_nb_out_led"][a + j] = dd[k] - dd[j]
    res = pd.DataFrame(out, index=x.index)
    return res.loc[df.index] if df.index.is_unique else res.iloc[np.argsort(x._i.values)].set_index(df.index)
