"""Assemble one HTML file per meeting: one section per race, charts and the summary table."""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

CSS = """
html,body{max-width:100%;overflow-x:hidden}
body{background:#0f1115;color:#e6e6e6;font-family:Inter,Helvetica,Arial,sans-serif;margin:0;padding:24px}
nav.races{position:sticky;top:0;background:#0f1115;padding:10px 0;border-bottom:1px solid #2a2f3a;z-index:2;
  display:flex;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch}
nav.races a{color:#e6e6e6;text-decoration:none;background:#1c2130;border:1px solid #2a2f3a;border-radius:16px;
  padding:8px 14px;white-space:nowrap;min-height:28px;font-size:14px}
.tablewrap{overflow-x:auto}
@media (max-width:700px){
  body{padding:12px}
  h1{font-size:22px} h2{font-size:18px;margin-top:28px}
  th,td{padding:8px 6px;font-size:13px}
  /* on a phone the table keeps what prices a race: runner, barrier, Neural, rated, price, move, value, flag */
  th.m,td.m{display:none}
  .facts span{display:block;margin:0 0 4px}
  table.narrow{min-width:0;width:100%}
}
h1{font-weight:600;margin:0 0 4px} h2{font-weight:600;margin:40px 0 8px;border-top:1px solid #2a2f3a;padding-top:24px}
.sub{color:#9aa0a6;margin-bottom:16px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;margin:12px 0 24px}
th,td{padding:6px 10px;border-bottom:1px solid #2a2f3a;text-align:right;white-space:nowrap}
th:first-child,td:first-child,th.l,td.l{text-align:left}
th{color:#9aa0a6;font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.flag-model{background:rgba(76,175,80,.18)} .flag-market{background:rgba(244,67,54,.18)}
.firm{color:#81c784} .drift{color:#e57373} .note{color:#9aa0a6;font-size:12px}
.chart{margin:8px 0 16px}
h3{font-weight:500;font-size:14px;color:#c9ced6;margin:20px 0 4px}
table.narrow{width:auto;min-width:420px}
.pos{color:#81c784} .neg{color:#e57373}
.facts{color:#c9ced6;margin:0 0 12px;font-size:14px} .facts span{margin-right:24px}
details.method{margin:0 0 16px} details.method summary{cursor:pointer;color:#9aa0a6;font-size:13px;min-height:28px}
"""


@dataclass
class SummaryRow:
    name: str
    barrier: int | None
    weight: float | None
    jockey: str | None
    days_since: int | None
    neural: float | None
    exp: float | None
    price: float | None
    opening: float | None
    market_prob: float | None
    model_prob: float | None
    flag: str | None  # model_higher | market_higher | None
    rated_price: float | None = None
    value_pts: float | None = None   # model minus market, probability points


@dataclass
class RaceSection:
    heading: str
    subheading: str
    figures: list[go.Figure] = field(default_factory=list)
    rows: list[SummaryRow] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)       # one-line readings under the heading: tempo, market %
    late_speed: list = field(default_factory=list)       # LateSpeedRow, ranked


def _fmt(v: Any, nd: int = 2, pct: bool = False) -> str:
    if v is None:
        return ""
    if pct:
        return f"{v*100:.1f}%"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return html.escape(str(v))


def _move(row: SummaryRow) -> str:
    if row.price is None or row.opening is None:
        return ""
    if row.price < row.opening:
        return '<span class="firm">firm</span>'
    if row.price > row.opening:
        return '<span class="drift">drift</span>'
    return "held"


def summary_table(rows: list[SummaryRow]) -> str:
    ordered = sorted(rows, key=lambda r: (r.neural is None, -(r.neural or 0)))
    head = ("<tr><th class='l'>Runner</th><th>Bar</th><th class='m'>Wt</th><th class='l m'>Jockey</th><th class='m'>Days</th>"
            "<th>Neural</th><th class='m'>EXP</th><th>Rated $</th><th>Price</th><th class='m'>Open</th><th>Move</th>"
            "<th class='m'>Market %</th><th class='m'>Neural %</th><th>Value</th><th>Flag</th></tr>")
    body = []
    for r in ordered:
        cls = {"model_higher": "flag-model", "market_higher": "flag-market"}.get(r.flag or "", "")
        flag = {"model_higher": "Neural > market", "market_higher": "market > Neural"}.get(r.flag or "", "")
        body.append(
            f"<tr class='{cls}'><td class='l'>{html.escape(r.name)}</td><td>{_fmt(r.barrier)}</td><td class='m'>{_fmt(r.weight,1)}</td>"
            f"<td class='l m'>{_fmt(r.jockey)}</td><td class='m'>{_fmt(r.days_since)}</td><td>{_fmt(r.neural,1)}</td><td class='m'>{_fmt(r.exp,1)}</td>"
            f"<td>{_fmt(r.rated_price)}</td><td>{_fmt(r.price)}</td><td class='m'>{_fmt(r.opening)}</td><td>{_move(r)}</td>"
            f"<td class='m'>{_fmt(r.market_prob,pct=True)}</td><td class='m'>{_fmt(r.model_prob,pct=True)}</td>"
            f"<td>{'' if r.value_pts is None else f'{r.value_pts:+.1f}'}</td><td>{flag}</td></tr>"
        )
    return f"<div class='tablewrap'><table>{head}{''.join(body)}</table></div>"


def late_speed_html(rows) -> str:
    """Ranked last-600m table beside the worm: to the 600 vs the last 600, vs class."""
    if not rows:
        return ""
    head = "<tr><th class='l'>Runner</th><th>To the 600m</th><th>Last 600m</th><th>Runs</th></tr>"
    body = []
    for r in rows:
        cls = "pos" if (r.last_600 or 0) > 0 else "neg" if (r.last_600 or 0) < 0 else ""
        body.append(f"<tr><td class='l'>{html.escape(r.name)}</td><td>{_signed(r.to_600)}</td>"
                    f"<td class='{cls}'>{_signed(r.last_600)}</td><td>{r.runs}</td></tr>")
    return ("<h3>Late speed, vs class (recency weighted, best last 600m first)</h3>"
            f"<div class='tablewrap'><table class='narrow'>{head}{''.join(body)}</table></div>")


def _signed(v: float | None) -> str:
    return "" if v is None else f"{v:+.2f}"


def render_meeting(title: str, subtitle: str, sections: list[RaceSection], method_note: str) -> str:
    parts = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
             f"<title>{html.escape(title)}</title><style>{CSS}</style>",
             # plotly.js is embedded (about 4 MB) so the report opens with no network.
             "<script>" + get_plotlyjs() + "</script></head><body>",
             f"<h1>{html.escape(title)}</h1><div class='sub'>{html.escape(subtitle)}</div>",
             f"<details class='method'><summary>How to read this page</summary><p class='note'>{html.escape(method_note)}</p></details>"]
    # Sticky race navigation: one tap per race on a phone.
    parts.append("<nav class='races'>" + "".join(
        f"<a href='#race-{i+1}'>{html.escape(s.heading.split(':')[0])}</a>" for i, s in enumerate(sections)) + "</nav>")
    for i, s in enumerate(sections):
        parts.append(f"<h2 id='race-{i+1}'>{html.escape(s.heading)}</h2><div class='sub'>{html.escape(s.subheading)}</div>")
        if s.facts:
            parts.append("<div class='facts'>" + "".join(f"<span>{html.escape(f)}</span>" for f in s.facts) + "</div>")
        for n in s.notes:
            parts.append(f"<p class='note'>{html.escape(n)}</p>")
        if s.rows:
            parts.append(summary_table(s.rows))
        for fig in s.figures:
            # The title lives in HTML so it wraps on a phone; plotly clips a long title inside the SVG.
            title = (fig.layout.title.text or "") if fig.layout.title else ""
            fig.update_layout(title=None, margin=dict(t=20))
            parts.append(f"<h3>{html.escape(title)}</h3>" if title else "")
            parts.append("<div class='chart'>" + pio.to_html(fig, full_html=False, include_plotlyjs=False,
                                                            config={"responsive": True, "displayModeBar": False}) + "</div>")
        if s.late_speed:
            parts.append(late_speed_html(s.late_speed))
    parts.append("</body></html>")
    return "".join(parts)
