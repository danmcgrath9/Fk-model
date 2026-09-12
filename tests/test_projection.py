import math

from fixtures import past_event, race_entry
from fk.projection import (Inputs, Params, ProjRace, fit_params, inputs_from_entry, kl_to_bsp, project, simulate, tempo_score,
                           win_probabilities)


def test_tempo_score_from_numbers_and_words():
    assert tempo_score({"min": "-0.19", "max": "-0.03"}) == round((-0.19 - 0.03) / 2 / 0.3, 12) or abs(tempo_score({"min": "-0.19", "max": "-0.03"}) + 0.3667) < 1e-3
    assert tempo_score({"min": "0.9", "max": "1.2"}) == 1.0                       # clamped
    assert tempo_score({"minCategory": "Slow", "maxCategory": "Average"}) == -0.5
    assert tempo_score({"description": "Fast"}) == 1.0 and tempo_score(None) == 0.0


def test_projection_arithmetic_by_hand():
    p = Params()
    # ratings oldest first 90, 92, 96, 101: weights 0.343, 0.49, 0.7, 1.0 (newest 1.0)
    # base = (90*.343 + 92*.49 + 96*.7 + 101*1) / 2.533 = (30.87 + 45.08 + 67.2 + 101) / 2.533 = 96.39
    inp = Inputs("h", "H", [90.0, 92.0, 96.0, 101.0], slope=3.5, starts=8, late600=1.0, settle=1.0)
    q = project(inp, tempo=-1.0, p=p)
    assert q.base == 101.0 and "rising" in q.note            # slope 3.5 >= 0.75 and last run above the mean: anchored at 101
    assert round(q.scope, 4) == round(1.5 * 4 / 12 + 0.5 * 2.0, 4)   # scope 0.5 + trend clamped to 2 x 0.5 = 1.5
    assert q.shape == -1.5                                    # backmarker in a slow race: -shape_weight
    assert q.late == 1.5                                      # +1 length late, slow tempo x1.5
    assert round(q.projected, 4) == round(101 + 1.5 - 1.5 + 1.5, 4)
    # sd: mean 94.75, squared deviations 22.5625 + 7.5625 + 1.5625 + 39.0625 = 70.75, /3 = 23.583, root 4.856 (>= floor 3)
    assert round(q.sd, 3) == 4.856
    steady = Inputs("s", "S", [90.0, 92.0, 96.0, 101.0], slope=0.2, starts=20, late600=None, settle=0.0)
    r = project(steady, tempo=-1.0, p=p)
    assert round(r.base, 2) == 96.39 and r.shape == 1.5 and r.late == 0.0 and r.scope == 0.1
    assert project(Inputs("n", "N", [], None, None, None, None), 0.0, p).projected is None


def test_win_probability_matches_the_closed_form_and_the_sim():
    from fk.projection import Projection
    a = Projection("a", "A", 100.0, 0, 0, 0, 100.0, 3.0, 5, "")
    b = Projection("b", "B", 97.0, 0, 0, 0, 97.0, 3.0, 5, "")
    probs = win_probabilities([a, b])
    expect = 0.5 * (1 + math.erf(3 / (3 * math.sqrt(2)) / math.sqrt(2)))   # Phi(0.7071) = 0.7602
    assert abs(probs["a"] - expect) < 1e-3 and abs(probs["a"] + probs["b"] - 1) < 1e-9
    sim = simulate([a, b], n=20000, seed=1)
    assert abs(sim["a"]["win"] - expect) < 0.01 and sim["a"]["place"] == 1.0
    none = Projection("c", "C", None, 0, 0, 0, None, None, 0, "no rated run")
    assert win_probabilities([a, b, none])["c"] is None


def test_inputs_from_entry_and_fit_moves_towards_bsp():
    e = race_entry("H1", "Quagmire", 3, result=1)
    e["form"] = {"careerForm": "8: 6-1-0"}
    inp = inputs_from_entry(e, predicted_position=2, field_size=9)
    assert inp.starts == 8 and inp.settle == 0.125 and inp.ratings and inp.late600 is not None
    assert inputs_from_entry(dict(e, scratched=True)) is None
    # a race where BSP has the first runner very short: the fit should shrink the spread
    r = ProjRace("r", [Inputs("a", "A", [100.0] * 4, 0.0, 20, None, None), Inputs("b", "B", [97.0] * 4, 0.0, 20, None, None)],
                 0.0, {"a": 0.9, "b": 0.1}, "a")
    wide = Params(sd_scale=2.2)
    fitted = fit_params([r], start=wide, sweeps=1)
    assert fitted.sd_scale < 2.2 and kl_to_bsp([r], fitted) < kl_to_bsp([r], wide)
