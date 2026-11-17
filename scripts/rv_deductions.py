"""Official Victorian scratching deductions for a day (16 Nov 2026, founder: "For all Official RV Deductions ...
www.racingvictoria.com.au/wagering/deductions"). That page embeds vicdeductions.betmakers.com, which reads the public
GraphQL endpoint below with the query copied from its own app. No credits, one request a day.

    python scripts/rv_deductions.py YYYY-MM-DD [TRACK]

Prints every scratching (race, saddlecloth, horse, time scratched, win and place deduction in cents, the scratched horse's
median price) and each race's total win deduction (the sum of its scratchings: what a bet struck before them all pays),
then a 'race, cents' block per track in the form of data/live_bets/<prefix>-deductions-actual.txt.
"""
from __future__ import annotations

import collections
import sys

import requests

URL = "https://ql.betmakers.com/query"
QUERY = """{
  meetingsDated(date: "%sT00:00:00.000Z") {
    id date track { name }
    races {
      name id status number startTime
      meeting { track { name } }
      deductionSet { status scratchedTabNo emergencyTabNo scratchedTime scratchedCompetitor { name tabNo } emergencyCompetitor { tabNo } }
      emergenciesFalse: deductionSet(include_emergencies: false) {
        scratchedMedianPrice
        deductions { type deduction scratchedMedianPrice }
      }
    }
  }
}"""

day = sys.argv[1]
want = sys.argv[2].lower() if len(sys.argv) > 2 else ""
r = requests.post(URL, json={"operationName": None, "variables": {}, "query": QUERY % day},
                  headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=30)
r.raise_for_status()
data = r.json()
if data.get("errors"):
    print("errors:", data["errors"]); sys.exit(1)
tot = collections.defaultdict(lambda: collections.defaultdict(float))
print(f"## Official Victorian deductions {day} (ql.betmakers.com, as on racingvictoria.com.au/wagering/deductions)\n")
print("| track | race | no. | scratched | time | win c | place c | median price | status |\n|---|---|---|---|---|---|---|---|---|")
for m in data["data"]["meetingsDated"] or []:
    tn = m["track"]["name"]
    if want and want not in tn.lower():
        continue
    for rc in sorted(m["races"], key=lambda x: x["number"]):
        if rc.get("status") == "ABANDONED":
            continue
        for i, d in enumerate(rc.get("deductionSet") or []):
            ef = (rc.get("emergenciesFalse") or [])[i] if i < len(rc.get("emergenciesFalse") or []) else {}
            win = place = 0.0; med = ef.get("scratchedMedianPrice")
            for x in ef.get("deductions") or []:
                if x["type"] == "WIN": win = float(x["deduction"] or 0)
                if x["type"] == "PLACE": place = float(x["deduction"] or 0)
            tot[tn][rc["number"]] += win
            print(f"| {tn} | R{rc['number']} | {d['scratchedCompetitor']['tabNo']} | {d['scratchedCompetitor']['name']} | "
                  f"{(d.get('scratchedTime') or '')[:16]} | {win:g} | {place:g} | {med} | {d.get('status')} |")
for tn, races in tot.items():
    print(f"\n### {tn}: total win deduction a race (a bet struck before every scratching)\nrace, cents")
    for rn in sorted(races):
        print(f"{rn}, {races[rn]:g}")
