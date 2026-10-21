"""Read an Ultimate A-League match page into match facts, events and one row per player.

Content: Ultimate A-League (ultimatealeague.com), CC BY 4.0.

A page carries:
  title       "<Home> vs <Away>. <stage>, <season>" (stage: Round N, Finals Week N, Pre-Season)
  details     date and time (local, with zone), stadium, referee, attendance, the score
  Timeline    events (goals, cards, ...) with minute, side and player, the icon's alt text saying which
  Lineups     rows of (home player, away player); a row holding only &nbsp; separates the starters from
              the bench; a player who came off carries <span class="match-sub-off">min</span>, one who
              came on <span class="match-sub-on">min</span>

parse_match(html) -> dict(match=..., events=[...], players=[...]); minutes on the pitch are worked out
from the substitutions and red cards and capped at 90, since bets settle on 90 minutes.
"""
import re

TITLE = re.compile(r'<title>\s*(.+?) vs (.+?)\. ([^,]+), (\d{4}-\d{2}) ::', re.S)  # stage: 'Round 7', 'Finals Week 1', 'Pre-Season'
PID = re.compile(r'player_id=(\d+)">([^<]+?)\s*(?:<small>\((\w+)\)</small>)?</a>')
SENDING_OFF = re.compile(r'red|second yellow', re.I)


def _minute(s):
    m = re.match(r'\s*(\d+)(?:\s*\+\s*(\d+))?', s or '')
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (None, 0)


def _detail(html, heading):
    m = re.search(r'<h2>' + heading + r'</h2>.*?<div class="detail-info-detail">\s*(.*?)\s*</div>', html, re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else None


def _cells(block):
    """The home and away cells of one row (event or line-up)."""
    out = {}
    for side in ('home', 'away'):
        m = re.search(r'id="match-event-team-' + side + r'" class="match-event-team([^"]*)">(.*?)(?=<div class="match-event-middle"|id="match-event-team-away"|$)',
                      block, re.S)
        if m and 'unused' not in m.group(1):
            out[side] = m.group(2)
    return out


def parse_match(html, match_id=None):
    t = TITLE.search(html)
    if not t:
        raise ValueError('not a match page (no title)')
    score = re.search(r'<div class="match-score">\s*<div>\s*(\d+)\s*-\s*(\d+)', html)
    att = _detail(html, 'Attendance')
    stage = t.group(3).strip()
    match = dict(ual_match_id=match_id, home=t.group(1).strip(), away=t.group(2).strip(),
                 round=stage.replace('Round ', ''), stage='Pre-Season' if 'pre-season' in stage.lower() else
                 'Finals' if 'final' in stage.lower() else 'Regular season',
                 season=t.group(4), when_local=_detail(html, 'Date'), stadium=_detail(html, 'Stadium'),
                 referee=_detail(html, 'Referee'),
                 attendance=int(re.sub(r'\D', '', att)) if att and re.search(r'\d', att) else None,
                 home_goals=int(score.group(1)) if score else None, away_goals=int(score.group(2)) if score else None,
                 completed='Completed' in html[:200000])

    ev_html = html.split('id="match-events"', 1)[1].split('id="match-players"', 1)[0] if 'id="match-events"' in html else ''
    events = []
    for block in re.split(r'<div class="match-event\s*"?\s*>', ev_html)[1:]:
        for side, cell in _cells(block).items():
            for d in re.findall(r'<div class="match-event-detail">(.*?)</div>\s*</div>', cell, re.S):
                alt = re.search(r'alt="([^"]+)"', d)
                tm = re.search(r'match-event-detail-time">([^<]*)<', d)
                pl = PID.search(d)
                minute, extra = _minute(tm.group(1) if tm else '')
                events.append(dict(ual_match_id=match_id, side=side, event=alt.group(1) if alt else None,
                                   minute=minute, stoppage=extra,
                                   player_id=int(pl.group(1)) if pl else None, player=pl.group(2).strip() if pl else None))

    lu_html = html.split('id="match-players"', 1)[1] if 'id="match-players"' in html else ''
    lu_html = lu_html.split('Notes:', 1)[0]
    players, bench = [], False
    for block in re.split(r'<div class="match-event">', lu_html)[1:]:
        if re.match(r'\s*&nbsp;\s*</div>', block):
            bench = True
            continue
        for side, cell in _cells(block).items():
            pl = PID.search(cell)
            if not pl:
                continue
            off = re.search(r'match-sub-off">([^<]*)<', cell)
            on = re.search(r'match-sub-on">([^<]*)<', cell)
            players.append(dict(ual_match_id=match_id, side=side, player_id=int(pl.group(1)), player=pl.group(2).strip(),
                                gk=(pl.group(3) or '').upper() == 'GK', starter=not bench,
                                sub_on=_minute(on.group(1))[0] if on else None,
                                sub_off=_minute(off.group(1))[0] if off else None))

    # minutes on the pitch within 90: from kick-off or coming on, to coming off, a sending-off, or 90
    red = {(e['side'], e['player_id']): e['minute'] for e in events if e['event'] and SENDING_OFF.search(e['event'])}
    for p in players:
        start = 0 if p['starter'] else p['sub_on']
        if start is None:
            p['minutes'] = 0
            continue
        end = min(x for x in (p['sub_off'], red.get((p['side'], p['player_id'])), 90) if x is not None)
        p['minutes'] = max(0, min(90, end) - min(90, start))
    return dict(match=match, events=events, players=players)
