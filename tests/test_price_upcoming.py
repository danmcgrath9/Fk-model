"""research/greyhound/topaz_price_upcoming.py: the bet window, the input families and the sealed card's shape."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_price_upcoming as PU  # noqa: E402
import topaz_v1 as V1              # noqa: E402


def test_bet_window_is_the_test_12_rule():
    assert PU.bet_window(0.25) == (8.0, 13.0)          # a 50% edge needs $6.00, so the band's floor rules
    assert PU.bet_window(0.15) == (10.0, 13.0)          # 1.5 / 0.15 = $10
    assert PU.bet_window(0.10) is None                  # needs $15, above the $13 band
    assert PU.bet_window(1.5 / 13) == (13.0, 13.0)        # exactly $13 needed: a one-price window


def test_every_model_input_has_a_family():
    cols = V1.NUM + [f"{c}_rel" for c in V1.REL] + ["pv_DANGER", "pv_len", "tip_rank", "tip_top", "mkt_lsp_mean5"]
    fams = {c: PU.family(c) for c in cols}
    assert fams["elo_rel"] == "who beat whom (Elo)" and fams["margin_elo"] == "who beat whom (Elo)"
    assert fams["pv_DANGER"] == "GRV's preview" and fams["tip_rank"] == "GRV's tips"
    assert fams["box"] == "box and the draw" and fams["box_ratio"] == "box and the draw"
    assert fams["time_rating_band_rel"] == "time and split ratings" and fams["mkt_lsp_mean5"] == "market history"
    unplaced = sorted(c for c, f in fams.items() if f == "other")
    assert len(unplaced) <= 6, unplaced


def test_card_payload_keeps_the_asked_track_and_all_the_edges():
    card = pd.DataFrame({"race_id": [1, 1, 1, 2, 2], "track_name": ["Sandown Park"] * 3 + ["Healesville"] * 2,
                         "track": ["SAP"] * 3 + ["HVL"] * 2, "race_number": [1, 1, 1, 4, 4],
                         "start_time": ["2026-11-05T19:00:00"] * 3 + ["2026-11-05T13:00:00"] * 2,
                         "distance": [515] * 3 + [300] * 2, "grade": ["Mixed 4/5"] * 3 + ["5"] * 2,
                         "box": [1, 2, 3, 1, 2], "dog_name": ["A", "B", "C", "D", "E"],
                         "p_model": [0.6, 0.3, 0.1, 0.8, 0.2], "grv_price": [1.9, 3.0, 9.0, 1.3, 10.0],
                         "topaz_rating": [98, 90, 80, 95, 85], "tip_rank": [1, 2, 0, 1, np.nan],
                         "is_best_bet": [True, False, False, False, False], "last5": ["11211", "2", "x", "1", "3"]})
    card["our_price"] = 1 / card.p_model
    book = card.groupby("race_id").grv_price.transform(lambda s: (1 / s).sum())
    contrib = np.array([[0.4, 0.1], [0.0, 0.1], [-0.4, -0.2], [0.3, 0.0], [-0.3, 0.0]])
    out = PU.card_payload(card, contrib, ["who beat whom (Elo)", "box and the draw"], book, "2026-11-05", 1000, ["SANDOWN"])
    assert out["tracks"] == ["Sandown Park"] and len(out["races"]) == 1 and out["races"][0]["d"] == 515
    r = out["races"][0]["r"]
    assert [x[1] for x in r] == ["A", "B", "C"] and r[0][5] == 1 and r[0][6] == 1 and r[1][5] == 2
    elo = out["fam"].index("who beat whom (Elo)")
    assert [elo, round(100 * (np.exp(0.4) - 1))] in r[0][8]
    # E at Healesville: 20% at $10 is a 100% edge inside $8-$13, kept as a paper bet though the track is not shown
    assert out["edges"] == [["Healesville", "4", "2", "E", 0.2, 10.0]]


def test_saved_model_predicts_the_same_after_align(tmp_path, monkeypatch):
    import topaz_walk as W
    rng = np.random.default_rng(0)
    n = 4000
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n),
                      "track": pd.Categorical(rng.choice(["MEP", "SAP"], n)),
                      "grade": pd.Categorical(rng.choice(["4", "5"], n)), "sex": pd.Categorical(rng.choice(["D", "B"], n))})
    race = pd.Series(np.repeat(np.arange(n // 8), 8))
    y = pd.Series(np.where(np.arange(n) % 8 == 0, 1.0, 0.0))
    monkeypatch.setattr(W, "ROUNDS_A", 20)
    bst = W.fit_fixed(X, y.values, race, np.ones(n), 20)
    monkeypatch.setattr(PU, "MODEL_DIR", tmp_path)
    bst.save_model(str(tmp_path / "model.txt"))
    (tmp_path / "meta.json").write_text('{"cols": ["a", "b", "track", "grade", "sex"], "fit_races": 500, "last_day": "x", "trained": "y"}')
    loaded, meta = PU.load_model()
    # tonight's frame has its columns in another order, one extra input and the categories as plain text
    tonight = X.assign(extra=1.0)[["extra", "sex", "b", "grade", "a", "track"]].astype({"track": str, "grade": str, "sex": str})
    Xa = PU.align(tonight, meta["cols"])
    assert list(Xa.columns) == meta["cols"]
    assert np.allclose(loaded.predict(Xa, raw_score=True), bst.predict(X, raw_score=True))
    assert loaded.predict(Xa, pred_contrib=True).shape == (n, 6)


def test_history_files_start_at_the_given_month(tmp_path):
    for n in ("runs_VIC_2019-12.json.gz", "runs_VIC_2020-01.json.gz", "races_VIC_2021-05.json.gz",
              "runs_VIC_upcoming.json.gz", "notes.txt"):
        (tmp_path / n).write_text("x")
    names = lambda fs: [f.name for f in fs]                                          # noqa: E731
    assert names(PU.history_files(tmp_path)) == ["races_VIC_2021-05.json.gz", "runs_VIC_2019-12.json.gz",
                                                 "runs_VIC_2020-01.json.gz", "runs_VIC_upcoming.json.gz"]
    assert names(PU.history_files(tmp_path, "2020-01")) == ["races_VIC_2021-05.json.gz", "runs_VIC_2020-01.json.gz",
                                                            "runs_VIC_upcoming.json.gz"]


def test_compare_prices_measures_two_builds_of_one_card():
    a = pd.DataFrame({"race_id": [1, 1, 2, 2], "dog": [10, 11, 20, 21], "p_model": [0.6, 0.4, 0.3, 0.7]})
    b = pd.DataFrame({"race_id": [1, 1, 2, 2], "dog": [10, 11, 20, 21], "p_model": [0.5, 0.5, 0.35, 0.65]})
    c = PU.compare_prices(a, b)
    # differences 0.1, 0.1, 0.05, 0.05; race 1's top pick ties in b (argmax takes the first, dog 10), race 2 agrees
    assert c["n"] == 4 and c["races"] == 2 and abs(c["mean_abs"] - 0.075) < 1e-12 and abs(c["max_abs"] - 0.1) < 1e-12
    assert c["top_same"] == 2 and c["corr"] > 0.9


def test_fetch_day_calls_every_race_at_once_and_keeps_the_card_order():
    import threading
    from greyhound.topaz import TopazClient
    sys.path.insert(0, os.path.dirname(__file__))
    from test_topaz import Resp

    races = [{"raceId": r, "meetingDate": "2026-11-06", "meetingId": 9, "trackCode": "SAN", "distance": 515,
              "incomingGrade": "5", "raceStart": f"2026-11-06T0{r}:00:00Z"} for r in (3, 1, 2)]

    class ByPath:                                   # answers by path, so thread order cannot matter
        def __init__(self):
            self.seen, self.lock = [], threading.Lock()

        def get(self, url, headers=None, params=None, timeout=None):
            with self.lock:
                self.seen.append(url.split("/v1/", 1)[-1] if "/v1/" in url else url)
            if url.endswith("race/upcoming"):
                return Resp(200, races)
            rid = int(url.rstrip("/").split("/race/")[1].split("/")[0])
            if url.endswith("/runs/form"):
                return Resp(200, [{"runId": rid * 10, "dogId": rid, "rating": 80, "startPrice": 3.0}])
            return Resp(200, [{"runId": rid * 10, "dogId": rid, "boxNumber": 1, "dogName": f"D{rid}"},
                              {"runId": rid * 10 + 1, "dogId": rid + 100, "boxNumber": None, "dogName": "reserve"}])

    s = ByPath()
    c = TopazClient("k", session=s, sleep=lambda _: None, max_per_minute=100000)
    rows, got_races, names = PU.fetch_day(c, "2026-11-06", workers=4)
    assert [r["raceId"] for r in rows] == [3, 1, 2]                  # /race/upcoming's order, one runner each
    assert all(r["rating"] == 80 and r["startPrice"] == 3.0 for r in rows)      # the form row merged by run
    assert c.calls == 7 and len(s.seen) == 7                         # upcoming + two a race


def test_rule_bets_blend_then_the_tested_rule(monkeypatch):
    # one race, our chances 50/50; GRV $1.50 and $6.00 (66.7% + 16.7%, so 80/20 with the book out); blend weights 1, 0
    monkeypatch.setenv("PRICE_BLEND", "1,0")
    card = pd.DataFrame({"race_id": [1, 1], "p_model": [0.5, 0.5], "grv_price": [1.5, 6.0], "track_name": ["X", "X"],
                         "track": ["X", "X"], "race_number": [1, 1], "box": [1, 2], "dog_name": ["A", "B"]})
    card["grv_pct"] = 1 / card.grv_price
    bets, w = PU.rule_bets(card)
    # blended $2.00 each; B's $6 is 3x it, A's $1.50 is not 1.3x. Kelly on 0.5 x 0.5 + 0.5 x 0.2 = 0.35 at $6:
    # (0.35 x 6 - 1) / 5 = 0.22, x75 = 16.5 units, capped at 4
    assert w == [1.0, 0.0] and len(bets) == 1
    assert bets[0][3] == "B" and bets[0][5] == 0.5 and bets[0][6] == 6.0 and bets[0][7] == 4.0
