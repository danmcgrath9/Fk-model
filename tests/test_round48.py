"""Round 48: the leads, each against the rest (topaz_round48)."""
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "greyhound"))
import topaz_round48 as R48  # noqa: E402
from test_round47 import field  # noqa: E402


def test_each_lead_splits_every_runner_into_its_listed_values():
    t = field(80)
    t.loc[:9, "to_jump"] = 50.0
    t.loc[10:19, "n_bet"] = 6
    out = R48.leads(t)
    for name, (lab, order) in out.items():
        assert len(lab) == len(t) and set(lab.unique()) <= set(order), name
    assert (out["TAB's first price to the jump, 48"][0] == "48 hours or more").sum() == 10
    assert (out["field at the bet"][0] == "6 or fewer").sum() == 10
    cls = out["class"][0]
    assert ((cls == "grade 5") == (t.race_class == 5)).all() and ((cls == "maiden") == (t.race_class == 8)).all()
    assert ((out["distance"][0] == "450 to 549 m") == ((t.distance >= 450) & (t.distance < 550))).all()


def test_the_table_takes_the_leads_and_the_halves(capsys):
    t = field(400)
    R48.R47.table(t, "2025-09-01", R48.HALVES, R48.leads(t))
    out = capsys.readouterr().out.splitlines()
    assert R48.HALVES[0] in out[0] and R48.HALVES[1] in out[0]
    rows = [r for r in out[2:] if r.startswith("| ")]
    assert rows and all(r.count("|") == 14 for r in rows) and rows[0].startswith("| every candidate | all |")
