"""The logical operations this project uses, named as the spec's operation summaries.

ONE place to correct if the spec names an operation differently: run
`python scripts/spec_report.py` to see every summary and operationId the spec
declares, then edit the strings here. fk.spec.find_operation matches on the
summary first and the operationId second, case-insensitively and ignoring
spaces, hyphens and underscores.
"""

UPCOMING_MEETINGS = "Get Upcoming Meetings"
RACE_FORM = "Get Race Form"
HORSE_PROFILE = "Get Horse Profile"
MEETING_SPEEDMAPS = "Get Meeting Speedmaps"
RACE_RESULTS = "Get Race Results"
RACE_ODDS = "Get Race Odds"

# Depth policy for horse profiles (Phase 0, item 3).
FIRST_SIGHT_BENCHMARKS = 10   # a horse we have never stored
KNOWN_HORSE_BENCHMARKS = 5    # a horse we hold, refreshed after each new start
RACE_FORM_BENCHMARKS = 10     # per race on the daily pull
