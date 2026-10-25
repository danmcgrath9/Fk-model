"""List the harness tracks in Betfair's free ANZ files, by state, with race counts (25 Oct 2026). Used to build
config/harness_au_tracks.txt, the Australian-venue filter for the opening-price recorder.

    python research/harness/list_tracks.py DIR [LABEL]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hx_data import read_all

df = read_all(sys.argv[1]).drop_duplicates(["WIN_MARKET_ID", "SELECTION_ID"])
g = df.groupby(["STATE_CODE", "TRACK"]).WIN_MARKET_ID.nunique().reset_index(name="races")
print("| state | track | races |\n|---|---|---|")
for r in g.sort_values(["STATE_CODE", "races"], ascending=[True, False]).itertuples():
    print(f"| {r.STATE_CODE} | {r.TRACK} | {r.races:,} |")
print("\nAUSTRALIAN TRACKS (uppercase, one per line):")
for t in sorted(g[g.STATE_CODE != "NZ"].TRACK.str.upper().unique()):
    print(t)
