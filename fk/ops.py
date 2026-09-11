"""The operations this project uses, named exactly as the spec's summaries (b2c-openapi.yaml 1.0.8).

fk.spec.find_operation matches on the summary, case-insensitively, ignoring spaces,
hyphens and underscores. `python scripts/spec_report.py` lists what the spec declares.
"""

UPCOMING_MEETINGS = "Get Upcoming Meetings"      # 1 credit; array of MeetingSummaryLite (races + lite entries)
MEETINGS_BY_DATE = "Get Meetings By Date"        # 1 credit; same shape for one DDMMYY
MEETING_SUMMARY = "Get Meeting Summary"          # 5 credits; every race with entries, ratings, odds, and results once run
MEETING_SPEEDMAPS = "Get Meeting Speedmaps"      # 5 credits; every race's speedmap in one call
RACE_FORM = "Get Race Form"                      # 2 credits + 0.5 per BenchmarkedRun beyond 5 per runner
HORSE_FORM = "Get Horse Form"                    # 2 credits + 0.5 per BenchmarkedRun beyond 5
USAGE_LOG = "Get Usage Log"                      # 1 credit; Form King's own record of what we were charged

# Depth policy. The credit model (spec, "API Credit Model") makes the first five
# BenchmarkedRun items per runner free on both Get Race Form and Get Horse Form, and
# charges 0.5 credits for each one beyond that, rounded up per response. So:
#   * Get Race Form at numBenchmarks=5 costs 2 credits a race and already carries every
#     runner's newest five benchmarked runs plus their full race career.
#   * A horse we have never held gets ONE Get Horse Form at numBenchmarks=10 (ceil(2 + 2.5)
#     = 5 credits) to fill in runs six to ten. After that, each race form refreshes the
#     newest five and the merge keeps the older ones, so a known horse costs nothing extra.
# Pulling every race form at numBenchmarks=10 instead costs 2 + 2.5 x runners per race
# (about 32 credits for a twelve-horse field) and re-buys the same deep runs every time the
# horse races. `daily_pull.py --race-benchmarks 10` still does that if you want it.
RACE_FORM_BENCHMARKS = 5
FIRST_SIGHT_BENCHMARKS = 10
FREE_BENCHMARKS_PER_RUNNER = 5
