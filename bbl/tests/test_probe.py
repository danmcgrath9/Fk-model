"""The probe's credit cap, against a fake Odds API that charges what the v4 docs say each call costs.

Not a test of the API (only a real response is): a test that the probe never asks for a call
that would pass MAX_CREDITS, and that a cap of 0 spends nothing.
"""
import importlib

import pytest


class FakeResp:
    def __init__(self, body, cost, used):
        self.status_code = 200
        self._body = body
        self.text = ''
        self.headers = {'x-requests-last': str(cost), 'x-requests-used': str(used), 'x-requests-remaining': str(20000 - used)}

    def json(self):
        return self._body


def fake_api():
    state = {'used': 1000}

    def get(url, params=None, timeout=None):
        path = url.split('/v4', 1)[1]
        markets = len((params or {}).get('markets', '').split(',')) if (params or {}).get('markets') else 0
        game = {'id': 'abcdef123', 'home_team': 'Heat', 'away_team': 'Strikers', 'commence_time': '2026-01-09T08:15:00Z'}
        if path == '/sports':
            cost, body = 0, [{'key': 'cricket_big_bash', 'group': 'Cricket', 'title': 'Big Bash', 'description': 'Big Bash League'}]
        elif path.endswith('/markets'):
            cost, body = 1, {'bookmakers': [{'key': 'sportsbet', 'markets': [{'key': 'h2h'}, {'key': 'player_runs'}]}]}
        elif path.startswith('/sports/') and path.endswith('/events'):
            cost, body = 0, [game]
        elif path.endswith('/events'):
            cost, body = 1, {'data': [game]}
        else:
            cost, body = 10 * markets, {'timestamp': 'x', 'data': [{'bookmakers': []}] if '/events/' not in path else {'bookmakers': []}}
        state['used'] += cost
        return FakeResp(body, cost, state['used'])

    return get, state


@pytest.mark.parametrize('cap', [0, 1, 45, 300])
def test_probe_never_passes_the_cap(cap, monkeypatch, tmp_path):
    monkeypatch.setenv('ODDS_API_KEY', 'test')
    monkeypatch.setenv('MAX_CREDITS', str(cap))
    monkeypatch.setenv('OUT', str(tmp_path))
    probe = importlib.reload(importlib.import_module('bbl.lines.probe'))
    get, state = fake_api()
    monkeypatch.setattr(probe.requests, 'get', get)
    probe.main()
    spent = state['used'] - 1000
    assert spent <= cap
    if cap == 0:
        assert spent == 0
    text = (tmp_path / 'PROBE.md').read_text()
    assert 'cricket_big_bash' in text and f'Credits spent this probe: {spent}' in text
