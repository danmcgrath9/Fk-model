"""The paper book's account: per-plan totals and the running profit chart.
Writes docs/PAPER_BOOK.md and reports/paper-book.html.

    python scripts/paper_report.py [--out reports]
"""
from __future__ import annotations

import argparse
import html as H
from datetime import datetime, timezone
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

from _common import load_settings
from fk import paper as P
from fk.db import Db
from fk.report.charts import DARK, _colour, phone
from fk.report.html import CSS, PAGE_JS

ROOT = Path(__file__).resolve().parents[1]


def chart(run: dict[str, list[tuple[str, float]]]) -> go.Figure:
    fig = go.Figure()
    for i, (plan, seq) in enumerate(sorted(run.items())):
        fig.add_trace(go.Scatter(x=list(range(1, len(seq) + 1)), y=[v for _, v in seq], mode="lines", name=plan,
                                 line=dict(color=_colour(i), width=2), hovertext=[lbl for lbl, _ in seq],
                                 hovertemplate=f"{plan}<br>%{{hovertext}}<br>%{{y:+.2f}} units<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#9aa0a6", width=1, dash="dash"))
    fig.update_layout(title="Running profit by plan, units, in bet order", xaxis=dict(title="Bets settled"),
                      yaxis=dict(title="Units", zeroline=False), **DARK)
    fig.update_layout(legend=dict(orientation="h", x=0, y=-0.25, yanchor="top"), height=460, margin=dict(l=50, r=20, t=60, b=110))
    phone(fig, 520)
    return fig


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "reports"))
    a = ap.parse_args()
    db = Db(load_settings().database_url)
    db.ensure_paper_book()
    bets = db.paper_bets()
    voids = [b for b in bets if b.get("void")]
    settled = [b for b in bets if b.get("settled_at") is not None and not b.get("void")]
    open_bets = [b for b in bets if b.get("settled_at") is None]
    summ = P.summarise(settled)
    struck = P.summarise_at_struck(settled)
    run = P.running(settled)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    days = sorted({str(b["meeting_date"]) for b in settled})

    lines = ["# Paper book", "", f"As at {stamp}. {len(settled)} bets settled over {len(days)} race days"
             f"{' (' + days[0] + ' to ' + days[-1] + ')' if days else ''}; {len(open_bets)} open; {len(voids)} void (the horse did not start, "
             "stake back, left out of every figure). Placed at the morning price on the page, settled at "
             "Betfair SP (starting price where there is no BSP); the struck-price column takes off bookmaker deductions for "
             "runners scratched after the bet. Nothing is bet for real.", "",
             "| plan | bets | winners | staked | returned | profit | return | at the struck price: profit | return |",
             "|---|---|---|---|---|---|---|---|---|"]
    rows_html = []
    for plan in P.PLANS:
        s = summ.get(plan)
        if not s:
            continue
        roi = f"{s.roi:+.1%}" if s.roi is not None else ""
        k = struck.get(plan)
        k_profit = f"{k.profit:+.1f}" if k else "n/a"
        k_roi = f"{k.roi:+.1%}" if k and k.roi is not None else "n/a"
        lines.append(f"| {plan} | {s.bets} | {s.winners} | {s.staked:.1f} | {s.returned:.1f} | {s.profit:+.1f} | {roi} | {k_profit} | {k_roi} |")
        cls = "pos" if s.profit > 0 else "neg" if s.profit < 0 else ""
        kcls = "pos" if k and k.profit > 0 else "neg" if k and k.profit < 0 else ""
        rows_html.append(f"<tr><td class='l'>{H.escape(plan)}<br><span class='tiny'>{H.escape(P.PLANS[plan])}</span></td><td>{s.bets}</td>"
                         f"<td>{s.winners}</td><td>{s.staked:.1f}</td><td>{s.returned:.1f}</td><td class='{cls}'>{s.profit:+.1f}</td><td class='{cls}'>{roi}</td>"
                         f"<td class='{kcls}'>{k_profit}</td><td class='{kcls}'>{k_roi}</td></tr>")
    # How the market moved after each bet was struck. A plan whose selections drift is one
    # the market disagrees with after we have backed them; one that firms has the late
    # money coming the same way.
    move = P.movement_summary(settled)
    move_rows = []
    if move:
        lines += ["", "## How the market moved after the bet", "",
                  "From the price the bet was struck at to the price it settled at (Betfair SP). "
                  "Firmed = the price shortened, the market came our way.", "",
                  "| plan | settled bets | median move | share that firmed |", "|---|---|---|---|"]
        for plan in P.PLANS:
            m = move.get(plan)
            if not m:
                continue
            lines.append(f"| {plan} | {m['n']} | {m['median']:+.1%} | {m['firmed_share']:.0%} |")
            cls = "pos" if m["median"] < 0 else "neg"
            move_rows.append(f"<tr><td class='l'>{H.escape(plan)}</td><td>{m['n']}</td>"
                             f"<td class='{cls}'>{m['median']:+.1%}</td><td>{m['firmed_share']:.0%}</td></tr>")
    # Races priced more than once before the one-snapshot rule: their later bets are the
    # union bias the rule now prevents, and they stay in the book, named rather than hidden.
    by_race: dict[str, set] = {}
    for b in bets:
        if b.get("race_id") and b.get("placed_at"):
            by_race.setdefault(b["race_id"], set()).add(str(b["placed_at"])[:10])
    multi = sorted(r for r, days in by_race.items() if len(days) > 1)
    if multi:
        lines += ["", f"{len(multi)} race(s) in the book were priced on more than one day, before a race was held to one "
                  "pricing: their bets are the union of the flags that appeared at each, which is not a rule anyone could "
                  "follow. They stay in the book and are named here: " + ", ".join(multi) + "."]
    lines += ["", "Plans: " + "; ".join(f"{k} = {v}" for k, v in P.PLANS.items()) + ".", "",
              "A plan needs a few hundred bets before its return means anything; the chart says how the sample is going, not whether it is over."]
    (ROOT / "docs" / "PAPER_BOOK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fig = chart(run)
    body = [f"<h1>Paper book</h1><div class='sub'>{len(settled)} bets settled over {len(days)} race days, {len(open_bets)} open. "
            "Placed at the morning price on the page, settled at Betfair SP. Nothing is bet for real.</div>",
            "<div class='tablewrap'><table><tr><th class='l'>Plan</th><th>Bets</th><th>Winners</th><th>Staked</th><th>Returned</th>"
            "<th>Profit</th><th>Return</th><th>Struck $: profit</th><th>Return</th></tr>"
            + "".join(rows_html) + "</table></div>",
            "<p class='note'>Two settlement bases. Profit settles at Betfair SP, which is what you get betting into the jump. "
            "Struck $ pays the price on the page when the bet went on, which is what you get taking that price at the time. "
            "They differ by however far the selections moved.</p>",
            "<h3>Running profit by plan, units, in bet order</h3>",
            "<div class='chart'><div class='bar'><button class='fs' type='button'>Full screen</button></div><div class='plot'>"
            + pio.to_html(fig.update_layout(title=None, margin=dict(t=20)), full_html=False, include_plotlyjs=False,
                          config={"responsive": True, "displayModeBar": False}) + "</div></div>",
            "<p class='note'>A plan needs a few hundred bets before its return means anything; this says how the sample is going, not whether it is over.</p>"]
    if move_rows:
        body += ["<h3>How the market moved after the bet</h3>",
                 "<div class='tablewrap'><table><tr><th class='l'>Plan</th><th>Settled bets</th><th>Median move</th>"
                 "<th>Share that firmed</th></tr>" + "".join(move_rows) + "</table></div>",
                 "<p class='note'>Struck price to Betfair SP. Firmed (green, negative) = the price shortened, the market came our way.</p>"]
    if multi:
        body.append(f"<p class='note'>{len(multi)} race(s) were priced on more than one day before a race was held to one "
                    "pricing; their bets are the union of the flags seen at each.</p>")
    if open_bets:
        by_day: dict[str, int] = {}
        for b in open_bets:
            by_day[str(b["meeting_date"])] = by_day.get(str(b["meeting_date"]), 0) + 1
        body.append("<p class='note'>Open: " + ", ".join(f"{d}: {n} bets" for d, n in sorted(by_day.items())) + "</p>")
    page = ("<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>Paper book</title><style>{CSS}</style><script>{get_plotlyjs()}</script></head><body>"
            + "".join(body) + f"<script>{PAGE_JS}</script></body></html>")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "paper-book.html").write_text(page, encoding="utf-8")
    print(f"paper book: {len(settled)} settled, {len(open_bets)} open; wrote {out / 'paper-book.html'} and docs/PAPER_BOOK.md")
    for plan, s in summ.items():
        print(f"  {plan:20} bets {s.bets:4}  staked {s.staked:7.1f}  profit {s.profit:+8.2f}  return {s.roi:+.1%}" if s.roi is not None else f"  {plan}")
    # One scoreboard per model: a plan's record means nothing across a change of model.
    by_model: dict[str, list[dict]] = {}
    for b in settled:
        by_model.setdefault(b.get("model") or "unrecorded", []).append(b)
    for model_name, group in sorted(by_model.items()):
        print(f"\nmodel: {model_name}")
        m_bsp, m_struck = P.summarise(group), P.summarise_at_struck(group)
        for plan, s in m_bsp.items():
            t = m_struck.get(plan)
            struck_txt = f"  at struck price {t.roi:+.1%}" if t and t.roi is not None else ""
            print(f"  {plan:20} bets {s.bets:4}  at BSP {s.roi:+.1%}{struck_txt}" if s.roi is not None else f"  {plan}")
    if voids:
        print(f"\n{len(voids)} void bets (did not start), left out of every figure")


if __name__ == "__main__":
    main()
