"""The running record (16 Nov 2026, founder: "just want you to keep a record of it"): the model's open book and the
9am list, every settled day, rebuilt from scratch on every run so it is safe to run after each settle.

    python3.13 running_record.py            writes data/live_bets/running-record.md and prints the totals

THE MODEL (the open book): every order on a meeting's sheet of record (<prefix>-betmatic-preopen.csv) that fills at Form
King's opening price, min_odds <= open <= max_odds, exactly as betmatic_html.py counts it. A WINNER IS PAID AFTER TAB'S
DEDUCTION FOR ITS RACE AS THE FOUNDER REPORTED IT (<prefix>-deductions-actual.txt, "race, cents"): paid = 1 + (open - 1) x
(1 - cents/100), the same sum the day page does (TIPPING_RULES.md, 1 Nov 2026: nothing is estimated, and a bet settles
at the price taken "unless the founder reports TAB's actual deduction for the race"). The first cut of this file (16 Nov)
left the reported deductions out and overstated five winners by 14.51u; the founder, 17 Nov: "Deductions? Are you
kidding?" No reported figure for a race = the price taken. Units as on the sheet. A runner with no finish (scratched
after the open) is void. Paper: not what BetMatic placed.

THE 9AM LIST: every horse in a <prefix>-9am.csv, settled at the price it was listed at, per bookie: won = to_win, lost =
minus stake_a_bookie. The founder bets it himself, so this assumes every listed horse was bet; a day he did not bet is
named in NOT_BET below and counted as no bet.
"""
import collections, csv, glob, math, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from opens import parse_opens

L = os.path.join(here, "../../data/live_bets")
OUT = os.path.join(L, "running-record.md")
UNIT = 50   # dollars a unit for the $ column (founder, 14 Nov 2026: "$50 units")
NOT_BET = set()   # 9am-list prefixes the founder did not bet, e.g. {"2026-11-14-sandown"}
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def finishes(path):
    fin = {}
    for l in open(path):
        m = re.match(r"R(\d+) (.+?)\s+finish (\S+)", l)
        if m:
            fin[(int(m[1]), norm(m[2]))] = m[3]
    return fin


def reported_deductions(P):
    """TAB's deduction per race as the founder reported it: {race: share of winnings}. No file, or no line = none."""
    out, f = {}, f"{L}/{P}-deductions-actual.txt"
    if os.path.exists(f):
        for l in open(f):
            pa = [x.strip() for x in l.split("#")[0].split(",")]
            if len(pa) >= 2 and pa[0].isdigit():
                out[int(pa[0])] = float(pa[1]) / 100
    return out


def open_book():
    rows = []
    for res in sorted(glob.glob(f"{L}/2026-*-results.txt")):
        P = os.path.basename(res)[:-len("-results.txt")]
        sheet, prices = f"{L}/{P}-betmatic-preopen.csv", f"{L}/{P}-prices.txt"
        if not (os.path.exists(sheet) and os.path.exists(prices)):
            continue
        px = {}
        for l in open(prices):
            pa = [x.strip() for x in l.split("#")[0].split(",")]
            if len(pa) >= 3 and pa[0].isdigit():
                scr = pa[2].upper().startswith("SCR")
                fk, tab = (None, None) if scr else parse_opens(", ".join(pa[3:]))
                px[(int(pa[0]), norm(pa[1]))] = (fk or tab, scr)
        fin = finishes(res)
        ded = reported_deductions(P)
        by = collections.OrderedDict()
        for o in csv.DictReader(open(sheet)):
            k = (int(o["race"]), norm(o["horse"]))
            op, scr = px.get(k, (None, True))
            if scr or op is None or op < float(o["min_odds"]) or (o.get("max_odds") and op > float(o["max_odds"])):
                continue
            b = by.setdefault(k, dict(horse=o["horse"], units=0.0, open=op))
            b["units"] += float(o["stake_units"])
        for k, b in by.items():
            f = fin.get(k)
            d = ded.get(k[0], 0.0)
            paid = 1 + (b["open"] - 1) * (1 - d)          # the price after TAB's reported deduction
            if f in (None, "None", "0"):
                res_, pl = "void", 0.0
            elif f == "1":
                res_, pl = "WON", b["units"] * (paid - 1)
            else:
                res_, pl = f"{f}th" if f not in ("2", "3") else {"2": "2nd", "3": "3rd"}[f], -b["units"]
            rows.append(dict(date=P[:10], meeting=P[11:], race=k[0], horse=b["horse"], units=b["units"], open=b["open"],
                             ded=d, paid=paid, result=res_, pl=pl))
    return rows


def nine_am():
    rows = []
    for f in sorted(glob.glob(f"{L}/2026-*-9am.csv")):
        P = os.path.basename(f)[:-len("-9am.csv")]
        res = f"{L}/{P}-results.txt"
        if not os.path.exists(res):
            continue
        fin = finishes(res)
        for r in csv.DictReader(open(f)):
            k = (int(r["race"]), norm(r["horse"]))
            fn = fin.get(k)
            if P in NOT_BET:
                res_, pl = "not bet", 0.0
            elif fn in (None, "None", "0"):
                res_, pl = "void", 0.0
            elif fn == "1":
                res_, pl = "WON", float(r["to_win"])
            else:
                res_, pl = {"2": "2nd", "3": "3rd"}.get(fn, f"{fn}th"), -float(r["stake_a_bookie"])
            rows.append(dict(date=r["date"], meeting=r["venue"], race=k[0], horse=r["horse"], price=float(r["take_at_or_above"]),
                             stake=float(r["stake_a_bookie"]), to_win=float(r["to_win"]), result=res_, pl=pl))
    return rows


def main():
    ob, nm = open_book(), nine_am()
    live = [r for r in ob if r["result"] != "void"]
    days = sorted({r["date"] for r in ob})
    out = ["# Running record", "",
           "Rebuilt by research/form_gbm/running_record.py after every settle (founder, 16 Nov 2026: \"just want you to keep a "
           "record of it\"). The model = the open book: every sheet-of-record order that fills at Form King's opening price, "
           "a winner paid after TAB's deduction for its race as the founder reported it (no figure reported = the price "
           "taken), units as on the sheet (paper, not what BetMatic placed). The 9am list = "
           "the founder's own bets at the listed price, per bookie, assuming every listed horse was bet.", ""]

    def line(sel, label):
        s = [r for r in live if sel(r)]
        st, pl, w = sum(r["units"] for r in s), sum(r["pl"] for r in s), sum(1 for r in s if r["result"] == "WON")
        return (f"| {label} | {len(s)} | {w} | {st:.2f}u | {pl:+.2f}u | {pl / st:+.0%} | ${pl * UNIT:+,.0f} |" if st
                else f"| {label} | 0 | 0 | - | - | - | - |")

    out += ["## The model (the open book)", "",
            "| Period | Bets | Won | Staked | P/L | ROI | At $50 |", "|---|---|---|---|---|---|---|",
            line(lambda r: True, f"All settled ({days[0] if days else '-'} on)"),
            line(lambda r: r["date"] >= "2026-11-12", "Since 12 Nov (full units)")]
    last7 = days[-7:]
    out += [line(lambda r: r["date"] in last7, "Last 7 race days"), "", "| Day | Bets | Won | Staked | P/L | ROI | At $50 |",
            "|---|---|---|---|---|---|---|"]
    out += [line(lambda r, d=d: r["date"] == d, d) for d in reversed(days)]
    run, cum = [], 0.0
    for d in days:
        cum += sum(r["pl"] for r in live if r["date"] == d); run.append((d, cum))
    out += ["", "Running total by day: " + ", ".join(f"{d[5:]} {c:+.1f}u" for d, c in run), "",
            "| Date | Meeting | Race | Horse | Units | Open | TAB deduction | Paid at | Result | P/L |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {r['date']} | {r['meeting']} | R{r['race']} | {r['horse']} | {r['units']:.2f}u | ${r['open']:g} | "
            f"{f'{r['ded'] * 100:.0f}c' if r['ded'] else '-'} | ${r['paid']:.2f} | {r['result']} | {r['pl']:+.2f}u |" for r in reversed(ob)]
    # Price taken against Betfair SP (founder, 16 Nov 2026: "Still beating open towards bsp though"): how many prices
    # beat BSP, the stake-weighted ratio, and winners against those expected at BSP (1/BSP each). The price is the open
    # AFTER TAB's reported deduction: BSP is struck after the scratching, so the open before it is not the same bet.
    bsp = {}
    for res in glob.glob(f"{L}/2026-*-results.txt"):
        P = os.path.basename(res)[:-len("-results.txt")]
        for l in open(res):
            m = re.match(r"R(\d+) (.+?)\s+finish \S+\s+SP \S+\s+BSP (\S+)", l)
            if m and m[3] not in ("None", "0.0", "0"):
                bsp[(P[:10], P[11:], int(m[1]), norm(m[2]))] = float(m[3])

    def clv(sel, label):
        s = [(r, bsp.get((r["date"], r["meeting"], r["race"], norm(r["horse"])))) for r in live if sel(r)]
        s = [(r, b) for r, b in s if b]
        if not s:
            return f"| {label} | 0 | - | - | - |"
        wl = sum(r["units"] * math.log(r["paid"] / b) for r, b in s) / sum(r["units"] for r, b in s)
        return (f"| {label} | {len(s)} | {sum(1 for r, b in s if r['paid'] > b)} | {math.exp(wl):.2f}x | "
                f"{sum(1 for r, b in s if r['result'] == 'WON')} won, {sum(1 / b for r, b in s):.1f} expected at BSP |")
    out += ["", "## Price taken against Betfair SP", "",
            "The price is the open after TAB's reported deduction.", "",
            "| Period | Bets with a BSP | Price beat BSP | Price / BSP (stake-weighted) | Winners |", "|---|---|---|---|---|",
            clv(lambda r: True, "All settled"), clv(lambda r: r["date"] >= "2026-11-12", "Since 12 Nov"),
            clv(lambda r: r["date"] in last7, "Last 7 race days")]
    bet = [r for r in nm if r["result"] not in ("void", "not bet")]
    tot = sum(r["pl"] for r in bet); w = sum(1 for r in bet if r["result"] == "WON")
    staked = sum(r["stake"] for r in bet)
    out += ["", "## The 9am list (the founder's bets, per bookie)", "",
            f"{len(bet)} bets, {w} won, staked ${staked:,.0f} a bookie, P/L ${tot:+,.0f} a bookie"
            + (f" ({tot / staked:+.0%})" if staked else "") + ".", "",
            "| Date | Meeting | Race | Horse | Take at | Stake a bookie | To win | Result | P/L a bookie |",
            "|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {r['date']} | {r['meeting']} | R{r['race']} | {r['horse']} | ${r['price']:.2f} | ${r['stake']:,.0f} | "
            f"${r['to_win']:,.0f} | {r['result']} | ${r['pl']:+,.0f} |" for r in reversed(nm)]
    open(OUT, "w").write("\n".join(out) + "\n")
    print("\n".join(out[7:12]))
    print(f"model: {len(live)} bets, {sum(1 for r in live if r['result'] == 'WON')} won, "
          f"{sum(r['pl'] for r in live):+.2f}u since {days[0] if days else '-'}; 9am list: {len(bet)} bets, {w} won, "
          f"${tot:+,.0f} a bookie -> {OUT}")


if __name__ == "__main__":
    main()
