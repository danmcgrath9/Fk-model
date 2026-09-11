"""Payloads shaped by b2c-openapi.yaml 1.0.8 (components.schemas). Not real data."""
from datetime import datetime, timezone

MS = 86400000


def ms(y, m, d):
    return int(datetime(y, m, d, 3, 0, tzinfo=timezone.utc).timestamp() * 1000)  # 13:00 or 14:00 Melbourne


def past_event(race_id, days_ago, *, with_benchmark=True, distance=1400, race=True):
    p = dict(raceId=race_id, date=ms(2026, 9, 12) - days_ago * MS, distance=distance, barrier=4, finishPosition=3, margin=1.5,
             posSettling=5, pos800m=5, pos400m=4, daysSincePreviousRace=14, gear=[], raceNumber=3, ratingScale="FORM_KING",
             tabMeeting=True, trackSpeed=1.2, trackSpeedVerified=days_ago % 2 == 0, race=race, scratched=False, startingPrice=6.5)
    if with_benchmark:
        p["benchmark"] = dict(
            age=4, atWeights=90.0, dataStage="FULL_SECTIONAL_DATA", finishingSpeed=102.3, firmOrDrift=1.0, meetingRunners=90,
            pir2=3, pir4=4, pir6=5, pir8=5, raceRating=95.0, raceRunners=12, railMetres=0.0, season="2026", sp=6.5,
            speedRating=101.0, vsAllAvg=0.5, vsClass=0.8, vsTrack=0.2, wfaRat=91.0,
            sections={"S-8": {"vsClass": -0.4}, "8-6": {"vsClass": 0.1}, "6-4": {"vsClass": 0.5}, "4-2": {"vsClass": 0.9},
                      "2-F": {"vsClass": 1.2}, "S-6": {"vsClass": -0.3}, "6-F": {"vsClass": 0.9}, "8-4": {"vsClass": 0.3}})
    return p


def race_entry(hid, name, number, *, n_benchmarks=5, n_events=8, odds=True, result=None):
    events = [past_event(f"PR{hid}{i}", 14 * (i + 1), with_benchmark=i < n_benchmarks) for i in range(n_events)]
    e = dict(breedingId=hid, horse={"name": name}, number=number, barrier=number, jockey=f"J {number}", trainer="T", scratched=False,
             weight=56.0, weightCarried=55.5, daysSinceLastRace=14, ratings={"neural": 60 + number, "exp": 58.0, "peak": 95.0, "peak12m": 93.0},
             pastEvents=events)
    if odds:
        e["odds"] = dict(avgNow=5.2, avgOpen=6.0, bestNow=5.5, bestBookies=["sportsbet"], firmOrDrift=2.4, timestamp=ms(2026, 9, 11))
    if result:
        e["horseResult"] = dict(barrier=number, bestToteWin=5.6, betfairPlaceDiv=1.9, betfairStartingPrice=5.8, finishPosition=result,
                                jockey=f"J {number}", margin=0.0 if result == 1 else 2.0, number=number, officialFlucs=[6.0, 5.5],
                                startingPrice=5.5, topFluc=6.5, totePlace=1.8, toteWin=5.4, weight=55.5)
    return e


def race_summary(mid="FLEM_120926", rid="FLEM_120926_3", n_runners=3, **kw):
    return dict(meetingId=mid, raceId=rid, number=3, name="Demo Handicap", distance=1400, going="Good", goingNumber=4, nightMeeting=False,
                prizemoneyGrade="MSAT", raceType="Flat", restrictions="BM78", status="FINAL_FIELDS", totalPrizeMoney=150000,
                trackCode="FLEM", startTime="13:30", syntheticHold=1.18, lws=92.0,
                entries=[race_entry(f"H{i}", f"Horse {i}", i + 1, **kw) for i in range(n_runners)])


def meeting_lite(mid="FLEM_120926", state="VIC", status="FINAL_FIELDS", date_ms=None, n_races=2):
    races = [dict(raceId=f"{mid}_{n}", number=n, name=f"Race {n}", distance=1200 + 200 * n, going="Good", goingNumber=4, nightMeeting=False,
                  prizemoneyGrade="MSAT", raceType="Flat", restrictions="", status=status, totalPrizeMoney=100000, trackCode="FLEM",
                  entries=[dict(barrier=i + 1, horse={"name": f"Horse {i}"}, jockey="J", number=i + 1, scratched=i == 2, trainer="T") for i in range(4)])
             for n in range(1, n_races + 1)]
    return dict(id=mid, date=date_ms if date_ms is not None else ms(2026, 9, 12), state=state, status=status, trackName="Flemington",
                tabMeeting=True, races=races)


def speedmap(rid="FLEM_120926_3"):
    return dict(raceId=rid, owner="formking", custom=False, direction="ANTI_CLOCKWISE",
                expectedTempo=dict(description="Average to Fast", minCategory="Average", maxCategory="Fast", min="-0.1", max="0.3"),
                entries=[dict(barrier=1, breedingId="H0", horse="Horse 0", number=1, daysSinceLastRace=14, distanceChange=0, emergency=False,
                              locked=False, runInPrep=2, earlySpeedValues=dict(overall=8.5, pir=2.0, type="SPEED_FIGURE"), medianEarlyVsBenchmark=1.1),
                         dict(barrier=2, breedingId="H1", horse="Horse 1", number=2, daysSinceLastRace=21, distanceChange=200, emergency=False,
                              locked=False, runInPrep=1, earlySpeedValues=dict(overall=4.0, pir=7.0, type="SPEED_FIGURE"), medianEarlyVsBenchmark=-0.8),
                         dict(barrier=3, breedingId="H2", horse="Horse 2", number=3, daysSinceLastRace=7, distanceChange=0, emergency=False,
                              locked=False, runInPrep=3, earlySpeedValues=dict(overall=8.5, pir=1.0, type="SPEED_FIGURE"), medianEarlyVsBenchmark=1.4)])
