"""greyhound/opens_join.py: recorded opens onto Topaz runs; only a known open counts; the book only when whole."""
import csv
import gzip

import numpy as np
import pandas as pd

from greyhound import opens_join as OJ


def test_join_by_date_venue_race_and_rug(tmp_path):
    rows = [  # race 3 at Sandown fully priced by the TAB; race 4 missing one runner; one later price and one other bookie
        dict(date="2026-11-04", venue="SANDOWN PARK", race=3, runner=1, bookie="TAB", open_known="True", first_price="2.50"),
        dict(date="2026-11-04", venue="SANDOWN PARK", race=3, runner=2, bookie="TAB", open_known="True", first_price="4.00"),
        dict(date="2026-11-04", venue="SANDOWN PARK", race=3, runner=3, bookie="TAB", open_known="True", first_price="8.00"),
        dict(date="2026-11-04", venue="SANDOWN PARK", race=3, runner=3, bookie="SPORTSBET", open_known="True", first_price="9.00"),
        dict(date="2026-11-04", venue="SANDOWN PARK", race=4, runner=1, bookie="TAB", open_known="True", first_price="3.00"),
        dict(date="2026-11-04", venue="SANDOWN PARK", race=4, runner=2, bookie="TAB", open_known="False", first_price="3.50"),
        dict(date="2026-11-04", venue="THE MEADOWS", race=1, runner=5, bookie="TAB", open_known="True", first_price="6.00")]
    with gzip.open(tmp_path / "opens-2026-11-04.csv.gz", "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    opens = OJ.load_opens(tmp_path)
    assert len(opens) == 7
    runs = pd.DataFrame({"race_id": [10, 10, 10, 11, 11, 12], "date": pd.Timestamp("2026-11-04"),
                         "track_name": ["Sandown"] * 5 + ["Meadows"], "race_number": [3, 3, 3, 4, 4, 1],
                         "box": [1, 2, 3, 1, 2, 5], "rug": [1, 2, 3, 1, np.nan, 5]})
    out, feats = OJ.join_opens(runs, opens)
    assert feats == ["open_price", "p_open"]
    assert out.open_price.tolist()[:3] == [2.5, 4.0, 8.0]
    # race 3: 1/2.5 + 1/4 + 1/8 = 0.775; runner 1's chance 0.4 / 0.775
    assert abs(out.p_open.iloc[0] - 0.4 / 0.775) < 1e-12 and abs(out.p_open.iloc[:3].sum() - 1) < 1e-12
    # race 4: runner 2's price was not an open, so the book is not whole: open_price kept for runner 1, no p_open
    assert out.open_price.iloc[3] == 3.0 and np.isnan(out.open_price.iloc[4]) and out.p_open.iloc[3:5].isna().all()
    # the Meadows alias, the rug falling back to the box, a one-dog race with an open is a whole book
    assert out.open_price.iloc[5] == 6.0 and out.p_open.iloc[5] == 1.0


def test_no_opens_at_all(tmp_path):
    runs = pd.DataFrame({"race_id": [1], "date": pd.Timestamp("2026-11-04"), "track_name": ["Geelong"], "race_number": [1], "box": [1]})
    out, _ = OJ.join_opens(runs, OJ.load_opens(tmp_path))
    assert np.isnan(out.open_price.iloc[0]) and np.isnan(out.p_open.iloc[0])
