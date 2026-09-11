"""Plotly figures for the report. Input is plain Python; nothing here reads JSON."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import plotly.graph_objects as go

DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0f1115",
    plot_bgcolor="#161a22",
    font=dict(family="Inter, Helvetica, Arial, sans-serif", size=13, color="#e6e6e6"),
    margin=dict(l=50, r=20, t=60, b=50),
    legend=dict(orientation="h", x=0, y=-0.34, yanchor="top", bgcolor="rgba(0,0,0,0)"),
    autosize=True,
)


@dataclass
class RunnerRuns:
    """A runner and its last N runs' per-section series, newest first."""
    horse_id: str
    name: str
    sections: list[str]                      # labels in running order
    runs: list[list[float | None]] = field(default_factory=list)  # newest first
    run_labels: list[str] = field(default_factory=list)           # e.g. dates, same order


def _pad(values: Sequence[float | None], n: int) -> list[float | None]:
    v = list(values)[:n]
    return v + [None] * (n - len(v))


def recency_weighted_mean(runs: list[list[float | None]], n_sections: int, decay: float = 0.8) -> list[float | None]:
    """Per-section mean over runs, newest weighted 1, then decay, decay^2 ...
    A section missing from a run is left out of that section's average, not zeroed."""
    out: list[float | None] = []
    for s in range(n_sections):
        num = den = 0.0
        for i, run in enumerate(runs):
            vals = _pad(run, n_sections)
            if vals[s] is None:
                continue
            w = decay ** i
            num += w * vals[s]
            den += w
        out.append(num / den if den > 0 else None)
    return out


# One colour per runner, shared by its latest and older runs, so the eye can follow a horse.
PALETTE = ["#4fc3f7", "#ff8a65", "#aed581", "#ba68c8", "#ffd54f", "#4db6ac", "#f06292", "#90a4ae",
           "#7986cb", "#a1887f", "#dce775", "#e57373", "#64b5f6", "#81c784", "#ffb74d", "#9575cd"]


def _colour(i: int) -> str:
    return PALETTE[i % len(PALETTE)]


def position_worm(runners: list[RunnerRuns], title: str) -> go.Figure:
    """One line per runner per run: position in running across the sections.
    The most recent run is drawn solid and wide; older runs faint. Lower is nearer the lead,
    so the y axis is reversed."""
    fig = go.Figure()
    for ri, r in enumerate(runners):
        for i, run in enumerate(r.runs):
            latest = i == 0
            fig.add_trace(
                go.Scatter(
                    x=r.sections,
                    y=_pad(run, len(r.sections)),
                    mode="lines+markers" if latest else "lines",
                    name=r.name if latest else f"{r.name} (older)",
                    legendgroup=r.horse_id,
                    showlegend=latest,
                    line=dict(width=3 if latest else 1, dash="solid" if latest else "dot", color=_colour(ri)),
                    opacity=1.0 if latest else 0.35,
                    hovertemplate=f"{r.name}<br>{r.run_labels[i] if i < len(r.run_labels) else ''}<br>%{{x}}: %{{y}}<extra></extra>",
                )
            )
    fig.update_layout(title=title, yaxis=dict(title="Position in running (1 = leader)", autorange="reversed"),
                      xaxis=dict(title="Race section"), **DARK)
    return fig


def sectional_worm(runners: list[RunnerRuns], title: str, last_600m_sections: int = 3, decay: float = 0.8) -> go.Figure:
    """One line per runner: recency-weighted vs-Class benchmark per section from their runs.
    Above zero is faster than class. The last 600m (final `last_600m_sections` sections) is shaded."""
    fig = go.Figure()
    for ri, r in enumerate(runners):
        avg = recency_weighted_mean(r.runs, len(r.sections), decay)
        fig.add_trace(
            go.Scatter(x=r.sections, y=avg, mode="lines+markers", name=r.name, line=dict(color=_colour(ri)),
                       hovertemplate=f"{r.name}<br>%{{x}}: %{{y:.2f}} vs class<extra></extra>")
        )
    fig.add_hline(y=0, line=dict(color="#9aa0a6", width=1, dash="dash"))
    if runners and last_600m_sections > 0 and len(runners[0].sections) >= last_600m_sections:
        secs = runners[0].sections
        fig.add_vrect(x0=secs[-last_600m_sections], x1=secs[-1], fillcolor="#ffb300", opacity=0.08,
                      line_width=0, annotation_text="last 600m", annotation_position="top left")
    fig.update_layout(title=title, yaxis=dict(title="vs Class (above 0 = faster than class)"),
                      xaxis=dict(title="Race section"), **DARK)
    return fig


@dataclass
class SpeedmapRunner:
    name: str
    predicted_position: float | None
    early_speed: float | None
    barrier: int | None = None


LANES = ["Leader", "On pace", "Midfield", "Off pace", "Backmarker"]


def lane_assignments(runners: list[SpeedmapRunner]) -> list[tuple[SpeedmapRunner, int, str]]:
    """(runner, rank, settling group) ordered by predicted early position, leader first.
    Runners with no predicted position are left off the map and named in the notes."""
    from .probability import settling_group
    mapped = [r for r in runners if r.predicted_position is not None]
    ordered = sorted(mapped, key=lambda r: r.predicted_position)  # type: ignore[arg-type]
    n = len(ordered)
    return [(r, i + 1, settling_group(i + 1, n)) for i, r in enumerate(ordered)]


def speedmap_chart(runners: list[SpeedmapRunner], title: str) -> go.Figure:
    """The Australian speed-map shape: a field map read left to right, the predicted leader
    furthest forward (right), each runner in its settling lane, labelled with its barrier,
    coloured by the early speed metric."""
    placed = lane_assignments(runners)
    fig = go.Figure()
    if placed:
        n = len(placed)
        speeds = [r.early_speed for r, _, _ in placed]
        fig.add_trace(
            go.Scatter(
                x=[n - rank + 1 for _, rank, _ in placed],   # leader at the right, like a field on the track
                y=[lane for _, _, lane in placed],
                mode="markers+text",
                text=[str(r.barrier) if r.barrier is not None else "" for r, _, _ in placed],
                textposition="middle center",
                textfont=dict(color="#0f1115", size=12),
                marker=dict(size=30, color=speeds, colorscale="Blues", showscale=any(v is not None for v in speeds),
                            colorbar=dict(title="Early speed", thickness=12), line=dict(color="#e6e6e6", width=1)),
                customdata=[[r.name, rank, r.early_speed if r.early_speed is not None else float("nan")] for r, rank, _ in placed],
                hovertemplate="%{customdata[0]}<br>predicted %{customdata[1]}th early, barrier %{text}<br>early speed %{customdata[2]:.1f}<extra></extra>",
                showlegend=False,
            )
        )
    fig.update_layout(
        title=title,
        xaxis=dict(title="Predicted early position, leader to the right", showticklabels=False, zeroline=False, showgrid=False),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(LANES)), title=""),
        **DARK,
    )
    fig.update_layout(height=380)
    return fig


def value_ladder(names: list[str], value_pts: list[float | None], title: str) -> go.Figure:
    """Betfair Hub's presentation: value % per runner, best value at the top, positive
    (model above market) in green, negative in red. Sign is also in the label."""
    rows = [(n, v) for n, v in zip(names, value_pts) if v is not None]
    rows.sort(key=lambda t: t[1], reverse=True)
    fig = go.Figure(
        go.Bar(
            x=[v for _, v in rows], y=[n for n, _ in rows], orientation="h",
            marker=dict(color=["#66bb6a" if v >= 0 else "#ef5350" for _, v in rows]),
            text=[f"{v:+.1f}" for _, v in rows], textposition="auto", cliponaxis=False, textangle=0, constraintext="none",
            hovertemplate="%{y}: %{x:+.1f} points<extra></extra>",
        )
    )
    fig.add_vline(x=0, line=dict(color="#9aa0a6", width=1))
    fig.update_layout(title=title, xaxis=dict(title="Value, probability points"),
                      yaxis=dict(autorange="reversed"), **DARK)
    return fig


def market_move_chart(names: list[str], opening: list[float | None], current: list[float | None] | None, title: str) -> go.Figure:
    """Firm and drift since opening, firmers first. Two inputs are accepted:
    * opening and current PRICES: the move is the % change in price (negative = firmed);
    * `current` None: `opening` already holds Form King's firmOrDrift in points of win
      chance, where POSITIVE is a firm; it is negated so firmers still sit left in green."""
    rows = []
    if current is None:
        for n, v in zip(names, opening):
            if v is not None:
                rows.append((n, -float(v), None, None))
        axis = "Form King firm or drift, points of win chance (negative = firmed)"
    else:
        for n, o, c in zip(names, opening, current):
            if o is None or c is None or o <= 0:
                continue
            rows.append((n, (c - o) / o * 100, o, c))
        axis = "% change in price since opening (negative = firmed)"
    rows.sort(key=lambda t: t[1])
    fig = go.Figure(
        go.Bar(
            x=[m for _, m, _, _ in rows], y=[n for n, _, _, _ in rows], orientation="h",
            marker=dict(color=["#66bb6a" if m < 0 else "#ef5350" if m > 0 else "#9aa0a6" for _, m, _, _ in rows]),
            text=[f"{m:+.0f}%" if current is not None else f"{-m:+.1f} pts" for _, m, _, _ in rows],
            customdata=[[o if o is not None else 0, c if c is not None else 0] for _, _, o, c in rows],
            textposition="auto", cliponaxis=False, textangle=0, constraintext="none",
            hovertemplate="%{y}: %{customdata[0]:.2f} to %{customdata[1]:.2f}, %{x:+.1f}%<extra></extra>",
        )
    )
    fig.add_vline(x=0, line=dict(color="#9aa0a6", width=1))
    fig.update_layout(title=title, xaxis=dict(title=axis), yaxis=dict(autorange="reversed"), **DARK)
    return fig


@dataclass
class LateSpeedRow:
    name: str
    to_600: float | None    # recency-weighted vs-Class averaged over the sections before the last 600m
    last_600: float | None  # the same over the last 600m sections
    runs: int


def late_speed_table(runners: list[RunnerRuns], last_600m_sections: int = 3, decay: float = 0.8) -> list[LateSpeedRow]:
    """The Punting Form read: the run to the 600 against the last 600, per runner, from the
    same recency-weighted means the worm draws. Ranked by last 600, best first."""
    rows = []
    for r in runners:
        n = len(r.sections)
        avg = recency_weighted_mean(r.runs, n, decay)
        split = max(n - last_600m_sections, 0)
        early = [v for v in avg[:split] if v is not None]
        late = [v for v in avg[split:] if v is not None]
        rows.append(LateSpeedRow(r.name, sum(early) / len(early) if early else None,
                                 sum(late) / len(late) if late else None, len(r.runs)))
    rows.sort(key=lambda x: (x.last_600 is None, -(x.last_600 or 0)))
    return rows


# ---- ratings profile -------------------------------------------------------------------------

@dataclass
class RunnerProfile:
    """Every rating Form King gave a runner, run by run, oldest first, plus the peaks."""
    name: str
    runs: list[dict]                 # fk.fields.run_ratings dicts, oldest first
    peak: float | None = None
    peak12m: float | None = None


def _rank_label(r: dict) -> str:
    rk = r.get("ranks") or {}
    parts = []
    if r.get("finish") is not None:
        n = f"/{r['runners']}" if r.get("runners") else ""
        parts.append(f"{int(r['finish'])}{n}")
    if rk.get("raceRank") is not None:
        parts.append(f"r{rk['raceRank']}")
    if rk.get("meetRatingRank") is not None:
        parts.append(f"m{rk['meetRatingRank']}")
    elif rk.get("meetRank") is not None:
        parts.append(f"m{rk['meetRank']}")
    return " ".join(parts)


def ratings_profile_chart(profiles: list[RunnerProfile], title: str) -> go.Figure:
    """Three panels sharing the run axis, one runner shown at a time (dropdown):
    1. Form King scale: rating at weights carried, WFA rating, market-expected rating,
       the race's rating, with the career and 12-month peaks as reference lines;
       beside each point the finish (3/12), the race rank (r) and meeting rank (m) of the
       last-600 section.
    2. Lengths vs class, track and all-average benchmarks (0 = par).
    3. Speed rating (100 = class par) and finishing speed (%, right axis).
    Trials are hollow markers."""
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07,
                        specs=[[{}], [{}], [{"secondary_y": True}]],
                        subplot_titles=("Form King ratings (peaks dashed)", "Lengths vs benchmark (0 = par)", "Speed rating (100 = par) and finishing speed %"))
    counts: list[int] = []
    for pi, p in enumerate(profiles):
        runs = p.runs
        x = [r.get("date") or "" for r in runs]
        sym = ["circle-open" if r.get("trial") else "circle" for r in runs]
        labels = [_rank_label(r) for r in runs]
        hover = [f"{r.get('date','')} {r.get('track','') or ''} {r.get('distance') or ''}m"
                 f"{' trial' if r.get('trial') else ''}<br>finish {r.get('finish')} of {r.get('runners')}<br>"
                 f"{'verified' if r.get('trackSpeedVerified') else 'unverified'} track speed" for r in runs]
        n0 = len(fig.data)
        c = _colour(pi)
        fig.add_trace(go.Scatter(x=x, y=[r.get("atWeights") for r in runs], name="At weights", mode="lines+markers+text", text=labels,
                                 textposition=["top center" if i % 2 == 0 else "bottom center" for i in range(len(runs))],
                                 textfont=dict(size=9), marker=dict(symbol=sym, size=8, color=c),
                                 line=dict(color=c, width=2), hovertext=hover, hovertemplate="%{hovertext}<br>at weights %{y}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=[r.get("wfaRat") if r.get("wfaRat") is not None else r.get("wfa") for r in runs], name="WFA rating",
                                 mode="lines+markers", marker=dict(symbol=sym, size=6), line=dict(color="#9aa0a6", width=1),
                                 hovertemplate="WFA %{y}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=[r.get("expected") for r in runs], name="Market expected", mode="lines+markers",
                                 marker=dict(symbol=sym, size=6), line=dict(color="#ffb74d", width=1, dash="dot"),
                                 hovertemplate="market expected %{y}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=[r.get("raceRating") for r in runs], name="Race rating", mode="markers",
                                 marker=dict(symbol="diamond-open", size=7, color="#e6e6e6"), hovertemplate="race rating %{y}<extra></extra>"), row=1, col=1)
        for val, nm, dash in ((p.peak, "Career peak", "dash"), (p.peak12m, "12-month peak", "longdash")):
            fig.add_trace(go.Scatter(x=x, y=[val] * len(x) if val is not None else [None] * len(x), name=nm, mode="lines",
                                     line=dict(color="#81c784" if nm == "Career peak" else "#4fc3f7", width=1, dash=dash),
                                     hovertemplate=f"{nm} %{{y}}<extra></extra>"), row=1, col=1)
        for key, nm, col in (("vsClass", "vs Class", c), ("vsTrack", "vs Track", "#9aa0a6"), ("vsAllAvg", "vs All average", "#ba68c8")):
            fig.add_trace(go.Scatter(x=x, y=[r.get(key) for r in runs], name=nm, mode="lines+markers", marker=dict(symbol=sym, size=6),
                                     line=dict(color=col, width=1.5 if key == "vsClass" else 1), hovertemplate=nm + " %{y:.2f} lengths<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=x, y=[r.get("speedRating") for r in runs], name="Speed rating", mode="lines+markers",
                                 marker=dict(symbol=sym, size=6), line=dict(color=c, width=1.5), hovertemplate="speed rating %{y}<extra></extra>"), row=3, col=1)
        fig.add_trace(go.Scatter(x=x, y=[r.get("finishingSpeed") for r in runs], name="Finishing speed %", mode="lines+markers",
                                 marker=dict(symbol=sym, size=6), line=dict(color="#ffb74d", width=1, dash="dot"),
                                 hovertemplate="finishing speed %{y:.1f}%<extra></extra>"), row=3, col=1, secondary_y=True)
        counts.append(len(fig.data) - n0)
    total = len(fig.data)
    buttons, start = [], 0
    for pi, p in enumerate(profiles):
        vis = [False] * total
        for i in range(start, start + counts[pi]):
            vis[i] = True
        buttons.append(dict(label=p.name, method="update", args=[{"visible": vis}]))
        start += counts[pi]
    for i, tr in enumerate(fig.data):
        tr.visible = i < (counts[0] if counts else 0)
    fig.add_hline(y=0, line=dict(color="#9aa0a6", width=1, dash="dash"), row=2, col=1)
    fig.add_hline(y=100, line=dict(color="#9aa0a6", width=1, dash="dash"), row=3, col=1)
    fig.update_layout(title=title, height=820, **DARK)
    fig.update_layout(legend=dict(orientation="h", x=0, y=-0.08), margin=dict(l=50, r=20, t=90, b=60),
                      updatemenus=[dict(type="dropdown", buttons=buttons, x=0, xanchor="left", y=1.12, yanchor="top",
                                        bgcolor="#1c2130", bordercolor="#2a2f3a", font=dict(color="#e6e6e6"))] if buttons else [])
    fig.update_xaxes(title_text="Run date", row=3, col=1)
    return fig
