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
  body{padding:8px}
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
.chart{margin:8px 0 16px;position:relative}
.chart .bar{display:flex;justify-content:flex-end;margin:0 0 2px}
.chart button.fs{min-height:44px;min-width:44px;padding:0 14px;background:#1c2130;color:#e6e6e6;border:1px solid #2a2f3a;
  border-radius:8px;font-size:14px;cursor:pointer}
.chart.full{position:fixed;inset:0;z-index:50;background:#0f1115;padding:8px;margin:0;overflow:auto;-webkit-overflow-scrolling:touch}
.chart.full .bar{position:sticky;top:0;background:#0f1115;z-index:2}
body.noscroll{overflow:hidden}
h3{font-weight:500;font-size:14px;color:#c9ced6;margin:20px 0 4px}
table.narrow{width:auto;min-width:420px}
.pos{color:#81c784} .neg{color:#e57373}
.trend-rising{color:#81c784} .trend-falling{color:#e57373} .trend-steady{color:#c9ced6} .trend-too{color:#5c6370}
table.strip td{white-space:nowrap;vertical-align:top;font-size:12px} td.trial{color:#6f7680} .tiny{font-size:11px;color:#9aa0a6}
.gear{color:#ffb74d}
.facts{color:#c9ced6;margin:0 0 12px;font-size:14px} .facts span{margin-right:24px}
details.method{margin:0 0 16px} details.method summary{cursor:pointer;color:#9aa0a6;font-size:13px;min-height:28px}
"""


# Phone sizing and full screen. A phone gets each chart at the height it asked for
# (layout.meta.phoneHeight) instead of the desktop height squeezed into 390px; every
# chart has a Full screen button that fills the viewport (turn the phone sideways for a
# wide chart) and scrolls inside itself when the chart needs more height than the screen.
PAGE_JS = """
(function(){
  var PHONE = window.innerWidth < 700;
  function meta(gd){ return (gd && gd.layout && gd.layout.meta) || {}; }
  // Plotly redraws the SVG at the new height but the graph div keeps its inline height,
  // so the next chart would draw over this one: size the box, then the plot.
  function setHeight(gd, h){
    gd.style.height = h + 'px';
    if (gd.parentElement) gd.parentElement.style.height = h + 'px';   // to_html's wrapper carries the inline height
    Plotly.relayout(gd, {height: h});
  }
  function plots(){ return Array.prototype.slice.call(document.querySelectorAll('.chart .js-plotly-plot')); }
  function sizePhone(){
    if (!PHONE) return;
    plots().forEach(function(gd){ var h = meta(gd).phoneHeight; if (h) setHeight(gd, h); });
  }
  function fitFull(chart){
    var gd = chart.querySelector('.js-plotly-plot'); if (!gd) return;
    var h = Math.max(window.innerHeight - 64, meta(gd).fullMinHeight || 0);
    setHeight(gd, h);
  }
  Array.prototype.forEach.call(document.querySelectorAll('.chart'), function(chart){
    var btn = chart.querySelector('button.fs'); var gd = chart.querySelector('.js-plotly-plot'); if (!btn || !gd) return;
    var base = null;
    btn.addEventListener('click', function(){
      var on = chart.classList.toggle('full');
      document.body.classList.toggle('noscroll', on);
      btn.textContent = on ? 'Close' : 'Full screen';
      if (on) { base = gd.layout.height; fitFull(chart); }
      else { setHeight(gd, base); }
    });
  });
  window.addEventListener('resize', function(){
    Array.prototype.forEach.call(document.querySelectorAll('.chart.full'), fitFull);
  });
  if (document.readyState === 'complete') sizePhone(); else window.addEventListener('load', sizePhone);
})();
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
    trend: str | None = None         # rising / steady / falling / too few runs (fk.trend)
    slope: float | None = None       # rating points per run over the last six rated runs
    last_rating: float | None = None
    best_rating: float | None = None
    finish: int | None = None          # official result, when the race has run
    result_sp: float | None = None
    horse_id: str | None = None


@dataclass
class FormStripRow:
    """A runner's recent runs, newest first, each a fk.fields.run_market dict."""
    name: str
    runs: list[dict]


@dataclass
class ProjectionRow:
    """One runner's projected figure and the sim, as the projection model built it."""
    name: str
    base: float | None
    scope: float
    shape: float
    late: float
    neural: float
    projected: float | None
    sd: float | None
    win: float | None       # exact chance
    place: float | None     # from the simulation
    rated: float | None
    note: str


@dataclass
class ContextRow:
    """What a form guide prints beside a runner that no chart holds."""
    name: str
    career: str | None
    track: str | None
    distance: str | None
    track_distance: str | None
    going: str | None            # form on today's going
    prep: str | None             # "2nd up: 4: 1-1-0"
    days_since_win: int | None
    jockey_win: float | None     # 12-month win %
    trainer_win: float | None
    combo: str | None            # jockey-horse combination form
    gear_changes: str | None
    ohr: float | None            # official handicap rating (benchmarkRating)
    distance_change: str | None
    age_sex: str | None
    prizemoney: float | None


@dataclass
class RaceSection:
    heading: str
    subheading: str
    figures: list[go.Figure] = field(default_factory=list)
    rows: list[SummaryRow] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)       # one-line readings under the heading: tempo, market %
    late_speed: list = field(default_factory=list)       # LateSpeedRow, ranked
    form_strip: list[FormStripRow] = field(default_factory=list)
    context: list[ContextRow] = field(default_factory=list)
    projections: list[ProjectionRow] = field(default_factory=list)
    sim_runs: int = 0
    bettable: bool = True        # False when the model's market input was incomplete: read, never bet


def _fmt(v: Any, nd: int = 2, pct: bool = False) -> str:
    if v is None:
        return ""
    if pct:
        return f"{v*100:.1f}%"
    if isinstance(v, float):
        out = f"{v:.{nd}f}"
        return out[1:] if out.startswith("-") and float(out) == 0 else out   # never "-0.0"
    return html.escape(str(v))


def _move(row: SummaryRow) -> str:
    if row.price is None or row.opening is None:
        return ""
    if row.price < row.opening:
        return '<span class="firm">firm</span>'
    if row.price > row.opening:
        return '<span class="drift">drift</span>'
    return "held"


def _result(r: SummaryRow) -> str:
    if r.finish is None:
        return ""
    n = int(r.finish)
    word = f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
    return word + (f" ${r.result_sp:.2f}" if r.result_sp else "")


def summary_table(rows: list[SummaryRow]) -> str:
    ordered = sorted(rows, key=lambda r: (r.neural is None, -(r.neural or 0)))
    run = any(r.finish is not None for r in rows)
    head = ("<tr><th class='l'>Runner</th>" + ("<th>Result</th>" if run else "") + "<th>Bar</th><th class='m'>Wt</th><th class='l m'>Jockey</th><th class='m'>Days</th>"
            "<th>Neural</th><th class='m'>EXP</th><th>Trend</th><th class='m'>Last</th><th class='m'>Best</th>"
            "<th>Rated $</th><th>Price</th><th class='m'>Open</th><th>Move</th>"
            "<th class='m'>Market %</th><th class='m'>Neural %</th><th>Value</th><th>Flag</th></tr>")
    body = []
    for r in ordered:
        cls = {"model_higher": "flag-model", "market_higher": "flag-market"}.get(r.flag or "", "")
        flag = {"model_higher": "Neural > market", "market_higher": "market > Neural"}.get(r.flag or "", "")
        body.append(
            f"<tr class='{cls}'><td class='l'>{html.escape(r.name)}</td>" + (f"<td class='{'pos' if r.finish == 1 else ''}'>{_result(r)}</td>" if run else "")
            + f"<td>{_fmt(r.barrier)}</td><td class='m'>{_fmt(r.weight,1)}</td>"
            f"<td class='l m'>{_fmt(r.jockey)}</td><td class='m'>{_fmt(r.days_since)}</td><td>{_fmt(r.neural,1)}</td><td class='m'>{_fmt(r.exp,1)}</td>"
            f"<td class='trend-{(r.trend or 'none').split()[0]}'>{_trend(r)}</td><td class='m'>{_fmt(r.last_rating,1)}</td><td class='m'>{_fmt(r.best_rating,1)}</td>"
            f"<td>{_fmt(r.rated_price)}</td><td>{_fmt(r.price)}</td><td class='m'>{_fmt(r.opening)}</td><td>{_move(r)}</td>"
            f"<td class='m'>{_fmt(r.market_prob,pct=True)}</td><td class='m'>{_fmt(r.model_prob,pct=True)}</td>"
            f"<td>{'' if r.value_pts is None else f'{r.value_pts:+.1f}'}</td><td>{flag}</td></tr>"
        )
    return f"<div class='tablewrap'><table>{head}{''.join(body)}</table></div>"


def _trend(r: SummaryRow) -> str:
    if not r.trend:
        return ""
    if r.slope is None:
        return html.escape(r.trend)
    slope = 0.0 if abs(r.slope) < 0.05 else r.slope
    return f"{html.escape(r.trend)} {slope:+.1f}"


def _run_cell(m: dict) -> str:
    """One past run as a form guide prints it: finish/field, margin, price, going, distance, track."""
    fin = f"{int(m['finish'])}" if m.get("finish") is not None else "?"
    fld = f"/{m['runners']}" if m.get("runners") else ""
    top = f"<b>{fin}{fld}</b>"
    # A trial has no market and its margin is not measured: Form King writes 0 for both,
    # and 0.0L at $0.00 would read as a dead-heat at no price.
    if not m.get("trial"):
        if m.get("margin") is not None:
            top += f" {m['margin']:.1f}L"
        if m.get("sp"):
            top += f" ${m['sp']:.2f}"
    from fk.report.charts import short_date
    bits = [str(m["going"]) if m.get("going") else "", f"{int(m['distance'])}m" if m.get("distance") else "",
            str(m["track"]) if m.get("track") else "", short_date(m["date"]) if m.get("date") else ""]
    low = " ".join(html.escape(b) for b in bits if b)
    cls = " class='l trial'" if m.get("trial") else " class='l'"
    tag = " trial" if m.get("trial") else ""
    return f"<td{cls}>{top}{html.escape(tag)}<br><span class='tiny'>{low}</span></td>"


def form_strip_html(rows: list[FormStripRow], n: int = 6) -> str:
    """Every runner's last n runs side by side, newest first, in the summary's order."""
    if not rows:
        return ""
    head = "<tr><th class='l'>Runner</th>" + "".join(f"<th class='l'>{'Last run' if i == 0 else f'{i+1} back'}</th>" for i in range(n)) + "</tr>"
    body = []
    for r in rows:
        cells = [_run_cell(m) for m in r.runs[:n]]
        cells += ["<td></td>"] * (n - len(cells))
        body.append(f"<tr><td class='l'>{html.escape(r.name)}</td>{''.join(cells)}</tr>")
    return ("<h3>Form strip: finish / field, margin, starting price, going, distance, track (newest first; trials greyed)</h3>"
            f"<div class='tablewrap'><table class='strip'>{head}{''.join(body)}</table></div>")


def projection_html(rows: list[ProjectionRow], sim_runs: int) -> str:
    """The projected figure per runner and where it came from, then the sim."""
    if not rows:
        return ""
    head = ("<tr><th class='l'>Runner</th><th>Base</th><th class='m'>Scope</th><th class='m'>Neural</th><th class='m'>Shape</th><th class='m'>Late</th>"
            "<th>Projected</th><th>&plusmn;</th><th>Win</th><th class='m'>Place</th><th>Rated $</th></tr>")
    body = []
    for r in sorted(rows, key=lambda r: (r.projected is None, -(r.projected or 0))):
        if r.projected is None:
            body.append(f"<tr><td class='l'>{html.escape(r.name)}</td><td colspan='10' class='l tiny'>{html.escape(r.note or 'no rated run')}</td></tr>")
            continue
        body.append(
            f"<tr><td class='l'>{html.escape(r.name)}{'<br><span class=tiny>' + html.escape(r.note) + '</span>' if r.note else ''}</td>"
            f"<td>{r.base:.1f}</td><td class='m'>{_signed(r.scope)}</td><td class='m'>{_signed(r.neural)}</td><td class='m'>{_signed(r.shape)}</td><td class='m'>{_signed(r.late)}</td>"
            f"<td><b>{r.projected:.1f}</b></td><td>{r.sd:.1f}</td><td>{_fmt(r.win, pct=True)}</td><td class='m'>{_fmt(r.place, pct=True)}</td>"
            f"<td>{_fmt(r.rated)}</td></tr>")
    return (f"<h3>Projected figure and the sim: base from recent runs, scope and Neural, race shape, late speed; "
            f"the race run {sim_runs:,} times. Rated $ here is the sim's own price</h3>"
            f"<div class='tablewrap'><table>{head}{''.join(body)}</table></div>")


def _pct(v: float | None) -> str:
    return "" if v is None else f"{v:.1f}%"


def context_html(rows: list[ContextRow]) -> str:
    """The rest of the form guide: records by track, distance and going, the run in the
    prep, the people, gear, the official rating."""
    if not rows:
        return ""
    head = ("<tr><th class='l'>Runner</th><th>Career</th><th class='m'>Track</th><th class='m'>Dist</th><th>T&amp;D</th><th>Going</th>"
            "<th>Prep</th><th class='m'>Last win</th><th>J win</th><th>T win</th><th class='m'>J/H combo</th><th>Gear</th>"
            "<th class='m'>OHR</th><th class='m'>Dist chg</th><th class='m'>Age/sex</th><th class='m'>Prize $</th></tr>")
    body = []
    for r in rows:
        prize = f"{r.prizemoney/1000:.0f}k" if r.prizemoney is not None else ""
        gear = f"<span class='gear'>{html.escape(r.gear_changes)}</span>" if r.gear_changes else ""
        body.append(
            f"<tr><td class='l'>{html.escape(r.name)}</td><td>{_fmt(r.career)}</td><td class='m'>{_fmt(r.track)}</td><td class='m'>{_fmt(r.distance)}</td>"
            f"<td>{_fmt(r.track_distance)}</td><td>{_fmt(r.going)}</td><td>{_fmt(r.prep)}</td><td class='m'>{_fmt(r.days_since_win)}</td>"
            f"<td>{_pct(r.jockey_win)}</td><td>{_pct(r.trainer_win)}</td><td class='m'>{_fmt(r.combo)}</td><td>{gear}</td>"
            f"<td class='m'>{_fmt(r.ohr,0)}</td><td class='m'>{_fmt(r.distance_change)}</td><td class='m'>{_fmt(r.age_sex)}</td><td class='m'>{prize}</td></tr>")
    return ("<h3>Runner context: records as starts: wins-seconds-thirds, the run in this prep, 12-month jockey and trainer win rates, gear changes</h3>"
            f"<div class='tablewrap'><table>{head}{''.join(body)}</table></div>")


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
            parts.append("<div class='facts'>" + " &middot; ".join(html.escape(f) for f in s.facts) + "</div>")
        for n in s.notes:
            parts.append(f"<p class='note'>{html.escape(n)}</p>")
        if s.rows:
            parts.append(summary_table(s.rows))
        if s.projections:
            parts.append(projection_html(s.projections, s.sim_runs))
        if s.context:
            parts.append(context_html(s.context))
        if s.form_strip:
            parts.append(form_strip_html(s.form_strip))
        for fig in s.figures:
            # The title lives in HTML so it wraps on a phone; plotly clips a long title inside the SVG.
            title = (fig.layout.title.text or "") if fig.layout.title else ""
            # DARK reserves 60px for a title; a chart that asked for more (a dropdown, subplot
            # titles) keeps what it asked for, every other chart closes up to the heading.
            t = fig.layout.margin.t
            fig.update_layout(title=None, margin=dict(t=20 if t is None or t <= 60 else t))
            parts.append(f"<h3>{html.escape(title)}</h3>" if title else "")
            parts.append("<div class='chart'><div class='bar'><button class='fs' type='button'>Full screen</button></div><div class='plot'>"
                         + pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True, "displayModeBar": False})
                         + "</div></div>")
        if s.late_speed:
            parts.append(late_speed_html(s.late_speed))
    parts.append("<script>" + PAGE_JS + "</script></body></html>")
    return "".join(parts)
