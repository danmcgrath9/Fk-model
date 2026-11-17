"""The corrected blend in the nightly run (topaz_iso): training rows, the kept card, and the bets at TAB's open."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_iso as I    # noqa: E402
import topaz_track as TR  # noqa: E402


def fact(dog, price, ran=True, won=0.0, bw="bw2", n="2", ded=0.0):
    return {"date": "2026-11-10", "bw_race": bw, "venue": "Healesville", "race_no": n, "start": "", "dog_name": dog,
            "price": price, "p_book": np.nan, "ran": ran, "s_later": 0.0, "n_later": 0, "ded": ded, "tab_first_t": "",
            "sportsbet_first": np.nan, "ladbrokes_first": np.nan, "won": won, "bsp": np.nan}


def iso_card(p=(0.4, 0.2, 0.2, 0.2), dogs=("Dog E", "Dog F", "Dog G", "Dog H")):
    return pd.DataFrame({"day": "2026-11-10", "race_key": "2026-11-10|Healesville|2", "venue": "Healesville",
                         "race_no": "2", "box": [str(i + 1) for i in range(len(dogs))], "dog_name": list(dogs),
                         "race_id": 7, "dog": [str(100 + i) for i in range(len(dogs))], "p_iso": list(p),
                         "x_elo": [1500.0, 1400, 1400, 1400], "x_track": ["HVL"] * len(dogs)})


def facts(prices=(4.5, 3.6, 3.6, 3.6), won=(1, 0, 0, 0)):
    f = pd.DataFrame([fact(d, p, won=w) for d, p, w in zip(("Dog E", "Dog F", "Dog G", "Dog H"), prices, won)])
    inv = 1 / f.price
    return f.assign(p_book=inv / inv.sum())


def test_at_open_uses_only_the_field_at_the_open_and_no_correction_is_the_blend():
    x = I.at_open(facts(), iso_card(), None, {"rounds": 0})
    assert len(x) == 4 and np.allclose(x.groupby("bw_race").p_corr.sum(), 1)
    assert np.allclose(x.p_corr, x.p_blend)
    # the blend at the held weights over ours and TAB's book at the open, by hand
    po, pt = np.array([0.4, 0.2, 0.2, 0.2]), (1 / x.price.values) / (1 / x.price.values).sum()
    s = 0.54 * np.log(po) + 0.67 * np.log(pt)
    assert np.allclose(x.p_blend.values, np.exp(s) / np.exp(s).sum())
    # a dog in TAB's field that is not on the card: the race is not priced
    f = pd.concat([facts(), pd.DataFrame([fact("Dog Z", 20.0)])], ignore_index=True)
    assert I.at_open(f, iso_card(), None, {"rounds": 0}).empty


def test_the_bets_are_the_corrected_chance_at_each_ratio():
    x = I.at_open(facts(prices=(5.2, 3.4, 3.4, 3.4)), iso_card(), None, {"rounds": 0})
    fair = 1 / x.p_corr.values
    for r in (1.1, 1.2):
        m = I.bets(x, r)
        assert (m == ((fair >= 2) & (fair < 15) & (x.price.values >= r * fair))).all()
    assert I.bets(x, 1.1).sum() >= I.bets(x, 1.2).sum()


def test_a_trained_correction_scores_at_the_open_with_categories_and_the_extra_inputs():
    import topaz_round41 as R41
    rng = np.random.default_rng(4)
    rows = []
    for r in range(600):
        p = rng.dirichlet(np.ones(4))
        w = rng.choice(4, p=p)
        for i in range(4):
            rows.append(dict(race_id=r, won=float(i == w), elo=rng.normal(1450, 50), track=["HVL", "SAN"][r % 2],
                             off=np.log(p[i]), lp_ours=np.log(p[i]), lp_tab=np.log(p[i]), gap=0.0, tab_book=1.3,
                             s_later=0.0, n_bet=4.0))
    R = pd.DataFrame(rows)
    XR = R[["elo", "track"] + I.EXTRA].assign(track=R.track.astype("category"))
    bst = R41.fit(XR, R.won.values, R.off.values, R.race_id.values, 20)
    meta = {"rounds": 20, "cols": list(XR.columns)}
    x = I.at_open(facts(), iso_card(), bst, meta)
    assert len(x) == 4 and np.allclose(x.groupby("bw_race").p_corr.sum(), 1)
    assert not np.allclose(x.p_corr, x.p_blend)                     # the trees moved it


def test_the_tracker_settles_the_corrected_bets_flat_at_tabs_first_price():
    card = TR.cards_from_payload({"day": "2026-11-10", "blend": [0.51, 0.66], "races": [
        {"t": "Healesville", "n": "2", "s": "", "r": [["1", "Dog E", 0.25, 4.0], ["2", "Dog F", 0.25, 4.0],
                                                       ["3", "Dog G", 0.25, 4.0], ["4", "Dog H", 0.25, 4.0]]}]})
    f = facts(prices=(5.2, 3.4, 3.4, 3.4))
    led, cov = TR.ledger(card, f, (iso_card(), None, {"rounds": 0}))
    c1, c2 = led[led.variant == "corr11"], led[led.variant == "corr12"]
    assert cov["corrected"] == 1 and len(c1) >= len(c2) >= 1
    a = c1[c1.dog_name == "Dog E"].iloc[0]
    assert a.units == 1.0 and a.status == "won" and np.isclose(a.units_won, a.paid - 1) and np.isclose(a.paid, 5.2)
    led0, cov0 = TR.ledger(card, f)                                     # no correction: variants 4 and 5 left out
    assert (led0.empty or not set(led0.variant) & {"corr11", "corr12"}) and "corrected" not in cov0


def test_out_of_sample_chances_take_the_walk_then_the_kept_cards(tmp_path):
    md, cd = tmp_path / "m", tmp_path / "c"
    md.mkdir()
    cd.mkdir()
    pd.DataFrame({"race_id": [1, 1, 2], "dog": ["5", "6", "7"], "p_a": [0.6, 0.4, 1.0], "p_b": [0.5, 0.5, 1.0]}).to_csv(
        md / "iso_walk.csv.gz", index=False)
    iso_card().assign(race_id=2, dog=["7", "8", "9", "10"]).to_csv(cd / "card_iso_2026-11-10.csv.gz", index=False)
    o = I.oos_chances(md, str(cd))
    assert set(o[o.race_id == 1].p_i) == {0.6, 0.4}
    assert np.isclose(o[(o.race_id == 2) & (o.dog == "7")].p_i.iloc[0], 0.4)       # the kept card wins race 2


def test_price_keeps_the_card_with_its_inputs(tmp_path, monkeypatch):
    import topaz_v1 as V1
    iso = tmp_path / "iso"
    iso.mkdir()
    monkeypatch.setenv("ISO_DIR", str(iso))
    day = "2026-11-18"
    t = pd.DataFrame({"date": pd.Timestamp(day), "race_id": [9] * 4, "dog": [11, 12, 13, 14], "box": [1, 2, 3, 4],
                      "dog_name": ["A", "B", "C", "D"], "track": "HVL", "track_name": "Healesville",
                      "race_number": 3, "elo": [1500.0, 1450, 1400, 1350], "grade": "5", "sex": "D"})

    class Booster:
        def predict(self, X, raw_score=True):
            return X.elo.values / 100

    monkeypatch.setattr(I, "load_model", lambda *a: (Booster(), {"cols": ["elo"] + list(V1.CAT)}))
    monkeypatch.setattr(I, "add_checks", lambda df, num, d: (df, num))
    seen = {}

    def build_day(cache, rows, races, d, since):
        seen["isolynx"] = os.environ.get("ISOLYNX_DIR")
        return t, ["elo"], [], "", None
    note = I.price(tmp_path, [], [], day, "2020-01", tmp_path / "cards", build_day, lambda v: "" if v is None else str(v))
    assert seen["isolynx"] == str(iso) and "ISOLYNX_DIR" not in os.environ       # set for the build only
    k = pd.read_csv(tmp_path / "cards" / f"card_iso_{day}.csv.gz", dtype={"dog": str})
    assert "4 runners" in note and list(k.race_key.unique()) == [f"{day}|Healesville|3"]
    assert np.isclose(k.p_iso.sum(), 1) and k.p_iso.iloc[0] == k.p_iso.max() and "x_elo" in k and "x_track" in k


def test_the_correction_fits_on_the_corrected_bsp_with_rounds_chosen_on_the_last_months(monkeypatch):
    import topaz_round41 as R41
    import topaz_round57 as R57
    monkeypatch.setattr(R41, "MAX_ROUNDS", 50)
    rng = np.random.default_rng(6)
    rows = []
    for r in range(1500):
        b = rng.dirichlet(np.full(5, 2.0))
        x = rng.normal(size=5)
        true = b * np.exp(0.4 * x)
        true /= true.sum()
        w = rng.choice(5, p=true)
        for i in range(5):
            rows.append(dict(race_id=r, won=float(i == w), date=pd.Timestamp("2024-11-01") + pd.Timedelta(days=r // 3),
                             off=np.log(b[i]), p_bsp=true[i], n_later=0, tip_rank=float(i == 0), weight_change=0.0,
                             x=x[i], lp_ours=np.log(b[i]), lp_tab=np.log(b[i]), gap=0.0, tab_book=1.3, s_later=0.0,
                             n_bet=5.0))
    R = R57.term_columns(pd.DataFrame(rows))
    XR = R[["x"] + I.EXTRA]
    bst, meta = I.fit_correction(R, XR)
    assert bst is not None and meta["rounds"] > 0 and meta["cols"] == ["x"] + I.EXTRA
    assert meta["races"] == 1500 and "the correction" in meta["check"]
