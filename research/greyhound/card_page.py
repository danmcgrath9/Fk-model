"""Tonight's card as a race page, in the shape of the gallops pages (5 Nov 2026, founder: "send me an artifact like
this", the Kyneton page): our own market for every dog, judged against TAB's opening price (founder, 5 Nov: "We need to base
them off TAB open ... create a market and then a kelly system of profit, more money the more the price is wrong ... at
1.3x 1.5x so on"), the races as tabs, one row per dog with our price, its TAB stake ladder and the model's reasons.

THE RULE (the gallops value rule of Test 21, at TAB's open): a bet when TAB opens the dog at 1.3x our price or more,
our price $2-$15. The stake is Kelly on a chance halfway between ours and TAB's (TAB's margin taken out: the race's own
book when every open is in, else TAB_BOOK), x75 units, at most 4. So the further TAB is out, the more units:
    units = 75 x (pk x price - 1) / (price - 1),   pk = 0.5 x ours + 0.5 x (1 / price) / book
1 unit is 1/75 of the betting bank.

    python research/greyhound/card_page.py CARD.json OUT.html [OPENS.json]

CARD.json is the payload topaz_price_upcoming.py seals, unsealed on the founder's side. OPENS.json (optional) maps
"race|DOG NAME" to [TAB open, TAB price when read] from the founder's own screenshots (by name, because a late
scratching moves a reserve into a box). Reserves (no box) leave the field and our chances are rescaled. The page holds GRV's values, so it
is never committed: it goes to a private artifact.
"""
import html
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

MEL = ZoneInfo("Australia/Melbourne")


def when(s: str) -> str:
    if not s:
        return ""
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return s
    t = t.astimezone(MEL) if t.tzinfo else t
    return t.strftime("%-I:%M%p").lower()


def money(x: float) -> str:
    return f"${x:,.2f}"


def title_case(name: str) -> str:
    return " ".join(w.capitalize() if not w.isupper() or len(w) > 2 else w.capitalize() for w in name.split())


RATIO, BAND, KELLY_X, CAP = 1.3, (2.0, 15.0), 75.0, 4.0
LADDER = (1.3, 1.5, 2.0, 3.0)
TAB_BOOK = 1.25          # TAB's open margin when a race's opens are not all in (Sandown R1, 5 Nov: 131% over 7 dogs)


def in_band(p: float) -> bool:
    """Our price inside the band the rule was tested on."""
    return p > 0 and BAND[0] <= 1 / p <= BAND[1]


def stake(p: float, price: float, book: float = TAB_BOOK) -> float:
    """Units to bet at `price` on a dog we give chance `p`: 0 unless price >= RATIO x ours and ours is in the band."""
    if not in_band(p) or not price or price <= 1 or price < RATIO / p - 1e-9:
        return 0.0
    pk = 0.5 * p + 0.5 * (1 / price) / max(book, 1.0)
    f = (pk * price - 1) / (price - 1)
    return float(min(max(KELLY_X * f, 0.0), CAP))


def ladder(p: float, book: float = TAB_BOOK) -> list:
    """[(multiple of our price, TAB price, units)] for each step of LADDER; empty outside the band."""
    if not in_band(p):
        return []
    return [(m, m / p, stake(p, m / p, book)) for m in LADDER]


def box_txt(b) -> str:
    """'2.0' -> '2' (the card carries boxes as the feed gives them)."""
    try:
        return str(int(float(b)))
    except (TypeError, ValueError):
        return str(b)


def ordinal(n: int) -> str:
    n = int(n)
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def units(u: float) -> str:
    return f"{u:.1f}u" if u else "0u"


def boxed(card: dict) -> dict:
    """Reserves (no box) only run after a scratching, so they leave the field and our chances are rescaled over the
    dogs with a box; GRV's book is recounted over the same dogs."""
    for r in card["races"]:
        kept = [x for x in r["r"] if str(x[0]).strip() not in ("", "nan")]
        total = sum(x[2] for x in kept) or 1.0
        for x in kept:
            x[0] = str(int(float(x[0])))
            x[2] = x[2] / total
        r["reserves"] = [title_case(x[1]) for x in r["r"] if str(x[0]).strip() in ("", "nan")]
        r["r"] = sorted(kept, key=lambda x: -x[2])
        r["b"] = sum(1 / x[3] for x in kept if x[3] > 1)
    return card


STYLE = """<style>
/* layout: one reading column, races as sticky tabs, a row per dog with the price as the left column */
:root{--bg:#fff;--fg:#1b1b1b;--mute:#5b5f58;--line:#e3e5e0;--chip:#eef0ec;--go:#1b5e20;--go2:#2e7d32;--no:#b71c1c;--warn:#e65100;--up:#1b5e20;--dn:#b71c1c;--paper:#37474f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121412;--fg:#ececea;--mute:#a4a8a1;--line:#30332f;--chip:#262925;--go:#2e7d32;--go2:#43a047;--no:#e57373;--warn:#ffb74d;--up:#81c784;--dn:#ef9a9a;--paper:#90a4ae;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121412;--fg:#ececea;--mute:#a4a8a1;--line:#30332f;--chip:#262925;--go:#2e7d32;--go2:#43a047;--no:#e57373;--warn:#ffb74d;--up:#81c784;--dn:#ef9a9a;--paper:#90a4ae;color-scheme:dark}
body{font:15px/1.45 -apple-system,system-ui,"Segoe UI",sans-serif;max-width:900px;margin:0 auto;padding-block:16px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));color:var(--fg);background:var(--bg)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
h1{font-size:22px;margin:0 0 4px;text-wrap:balance}
.sub{color:var(--mute);font-size:13px;margin-bottom:14px}
h2{font-size:18px;margin:26px 0 6px;border-bottom:2px solid var(--fg);padding-bottom:4px;scroll-margin-top:64px;text-wrap:balance}
.hd{color:var(--mute);font-size:13px;margin-bottom:6px}
.r{display:grid;grid-template-columns:76px 1fr;gap:4px 12px;padding:10px 0;border-bottom:1px solid var(--line)}
.r>div{min-width:0}
.px{font-weight:700;font-size:18px;font-variant-numeric:tabular-nums}
.pc{display:block;font-weight:400;font-size:12px;color:var(--mute)}
.nm{font-weight:600}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:3px;margin-left:6px;vertical-align:middle;background:var(--chip);color:var(--fg)}
.edge{background:var(--go);color:#fff}.no{background:var(--no);color:#fff}.bb{background:var(--paper);color:#fff}
.mk{font-size:12.5px;color:var(--mute)}
.why{grid-column:2;font-size:13.5px}
.why b{font-weight:600}
.up{color:var(--up)}.dn{color:var(--dn)}
.nav{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);display:flex;gap:6px;overflow-x:auto;padding:8px 0;margin:0 0 12px;border-bottom:1px solid var(--line);-webkit-overflow-scrolling:touch}
.nav a{flex:0 0 auto;min-width:44px;text-align:center;padding:9px 10px;border-radius:6px;background:var(--chip);color:var(--fg);text-decoration:none;font-weight:600;font-size:14px}
.nav a.hb{background:var(--go);color:#fff}
.nav a:focus-visible,.r a:focus-visible{outline:2px solid var(--go2);outline-offset:2px}
.bets{border:2px solid var(--go);border-radius:8px;padding:12px 14px;margin:0 0 18px;scroll-margin-top:64px}
.bets h2{margin:0 0 8px;border:0;padding:0;font-size:17px}
.tw{overflow-x:auto}
.bets table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
.bets td,.bets th{padding:6px 4px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.bets td:first-child,.bets th:first-child{text-align:left;white-space:normal}
.bets .dn{display:block;font-size:13px;color:var(--mute)}
.bets .u{display:block;font-size:12px;color:var(--mute)}
.lad{font-variant-numeric:tabular-nums}
.lad b{color:var(--go)}
@media (max-width:430px){.bets{padding:10px 8px}.bets table{font-size:13px}.bets td,.bets th{padding:6px 3px}}
.bets th{font-size:12px;color:var(--mute);font-weight:600}
.bets a{color:var(--fg);white-space:nowrap}
.note{font-size:12.5px;color:var(--mute);margin-top:8px}
.mh{margin:34px 0 0;scroll-margin-top:64px}.mh h2{margin:0 0 6px;font-size:21px;border-bottom:3px solid var(--go)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 6px}.chips a{min-width:44px;text-align:center;padding:7px 9px;border-radius:6px;background:var(--chip);color:var(--fg);text-decoration:none;font-weight:600;font-size:13px}
.chips a.hb{background:var(--go);color:#fff}
h3{font-size:17px;margin:22px 0 4px;border-bottom:2px solid var(--fg);padding-bottom:3px;scroll-margin-top:64px}
</style>"""


def slug(t: str) -> str:
    return "".join(ch for ch in t.lower() if ch.isalnum()) or "track"


def short(t: str) -> str:
    return t.replace(" Park", "").replace("The ", "")


def anchor(r: dict) -> str:
    return f"{slug(r['t'])}-r{r['n']}"


def page(card: dict, opens: dict, made: str, now: datetime | None = None) -> str:
    """The page; `now` (aware) leaves races already started out of the watch list, never out of the card."""
    card = boxed(card)
    fam = card["fam"]
    races = card["races"]
    tracks = card["tracks"]
    single = len(tracks) == 1
    name = tracks[0] if single else "Victorian dogs"
    day = datetime.fromisoformat(card["day"]).strftime("%a %-d %b")

    def op_for(r, dog):
        return opens.get(f"{r['t']}|{r['n']}|{dog.upper()}") or (opens.get(f"{r['n']}|{dog.upper()}") if single else None)

    def race_book(r):
        """TAB's open book for the race when every dog's open is in, else TAB_BOOK."""
        ops = [op_for(r, x[1]) for x in r["r"]]
        return sum(1 / o[0] for o in ops) if ops and all(o and o[0] > 1 for o in ops) else TAB_BOOK

    # the watch list: dogs GRV's pre-race price already has at 1.3x ours or more, the likeliest to open long on TAB
    def started(r):
        try:
            return now is not None and datetime.fromisoformat(r["s"].replace("Z", "+00:00")) <= now
        except (ValueError, AttributeError):
            return False

    watch_all = [(r, x) for r in races for x in r["r"] if in_band(x[2]) and x[3] and x[3] >= RATIO / x[2]]
    watch = [w for w in watch_all if not started(w[0])]
    gone = len(watch_all) - len(watch)
    watch.sort(key=lambda t: (t[0]["s"], -t[1][3] * t[1][2]))
    meetings = {}
    for r in races:
        meetings.setdefault(r["t"], []).append(r)
    order = sorted(meetings, key=lambda t: min(r["s"] for r in meetings[t]))
    with_bet = {w[0]["t"] for w in watch}
    out = []
    a = out.append
    a(f"<title>{html.escape(name)} {day}, prices {made}</title>")
    a('<meta name="claude:viewport-fit-sides" content="cover">')
    a(STYLE)
    a(f"<h1>{html.escape(name)} {day}, prices {made}</h1>")
    a(f"<div class='sub'>Our market: every dog priced by our model, adding to 100% a race (fitted on {card['fit']:,} "
      f"Victorian races, {card['rounds']:,} rounds, with GRV's preview, tips and rating). "
      + ("" if single else f"{len(order)} meetings, {len(races)} races, in TAB's order under each meeting. ")
      + "Melbourne time. Nothing here has been bet.</div>")
    rule = sorted(card.get("bets") or [], key=lambda b: next((r["s"] for r in races if r["t"] == b[0] and r["n"] == b[1]), ""))
    if card.get("bets") is not None:
        bw = card.get("blend") or [0.51, 0.66]
        a("<div class='bets' id='rule'><h2>The tested rule's bets ({}, {:.0f} units)</h2><div class='tw'><table>".format(
            len(rule), sum(b[7] for b in rule)))
        a("<tr><th>Race</th><th>Ours</th><th>Bet at</th><th>GRV</th><th>Units</th></tr>")
        for b in rule:
            r = next((r for r in races if r["t"] == b[0] and r["n"] == b[1]), None)
            jumps = when(r["s"]) if r else ""
            link = f"<a href='#{anchor(r)}'>{html.escape(short(b[0]))} R{b[1]}</a>" if r else f"{html.escape(short(b[0]))} R{b[1]}"
            a(f"<tr><td>{link} {jumps}<span class='dn'>{html.escape(box_txt(b[2]))}. {html.escape(title_case(b[3]))}</span></td>"
              f"<td>{money(1 / b[4])}</td><td><b>{money(RATIO / b[5])}+</b></td><td>{money(b[6])}</td><td><b>{units(b[7])}</b></td></tr>")
        if not rule:
            a("<tr><td colspan='5' style='text-align:left'>No dog meets the rule today.</td></tr>")
        a(f"</table></div><div class='note'>The rule as tested in Test 27's walk-forward (+58% flat, +70% Kelly at "
          f"GRV's SP over 29 months, 27 in profit): our chance blended with GRV's ({bw[0]:.2f} / {bw[1]:.2f}), a bet "
          "when GRV's price is at least 1.3x the blended price, the blended price $2-$15, Kelly x75 on the chance halfway "
          "between the blend and GRV's, up to 4 units. Bet at: 1.3x the blended price, so take any price at or above it "
          "(TAB's open included). GRV's pre-race price stands in for the SP here, and it is not the "
          "SP; drop a dog that drifts 30% from its shortest price before the jump. Paper.</div></div>")
    a("<div class='bets' id='bets'><h2>Check these at TAB's open ({})</h2>".format(len(watch))
      + (f"<div class='hd'>{gone} more in races already run, left out</div>" if gone else "") + "<div class='tw'><table>")
    a("<tr><th>Race</th><th>Ours</th>" + "".join(f"<th>TAB {m:g}x</th>" for m in LADDER[:3]) + "</tr>")
    for r, x in watch:
        op = op_for(r, x[1])
        bk = race_book(r)
        cells = "".join(f"<td>{money(pr)}<span class='u'>{units(u)}</span></td>" for m, pr, u in ladder(x[2], bk)[:3])
        got = ""
        if op:
            u = stake(x[2], op[0], bk)
            got = (f"<span class='dn'>TAB opened {money(op[0])}: {op[0] * x[2]:.2f}x, "
                   + (f"<b>{units(u)}</b>" if u else "no bet") + "</span>")
        a(f"<tr><td><a href='#{anchor(r)}'>{html.escape(short(r['t']))} R{r['n']}</a> {when(r['s'])}"
          f"<span class='dn'>{html.escape(title_case(x[1]))} (GRV {money(x[3])})</span>{got}</td>"
          f"<td><b>{money(1 / x[2])}</b></td>{cells}</tr>")
    if not watch:
        a("<tr><td colspan='5' style='text-align:left'>GRV's pre-race prices have no dog at 1.3x ours today: check "
          "each race's ladder below against TAB's open.</td></tr>")
    a("</table></div><div class='note'><b>How to bet it:</b> when TAB opens a dog at the price in a column or longer, "
      "bet the units under it (1 unit = 1/75 of your bank: a $750 bank makes a unit $10). The further TAB is above "
      "our price, the more units, up to 4. The stake is Kelly on a chance halfway between ours and TAB's, with TAB's "
      "margin taken out, because our model alone is weaker than the market: 1.3x is a small bet, 2x a big one. "
      "Every dog priced $2-$15 by us has its own ladder in its race below; these are the ones GRV's pre-race price "
      "already has long, so look at them first. Don't add to or re-take a dog that drifts 30% from its shortest price "
      "before the jump (Test 25). This rule made +55% / +48% at GRV's SP (Test 21) and has never been tested at TAB's "
      "open: that needs the opens recorded. Paper: nothing goes to BetMatic without your OK.</div></div>")
    a("<nav class='nav'>" + ("<a href='#rule' class='hb'>Rule</a>" if card.get("bets") is not None else "") + "<a href='#bets' class='hb'>TAB</a>" + "".join(
        f"<a href='#m-{slug(t)}'{' class=\"hb\"' if t in with_bet else ''}>{html.escape(short(t))}</a>" for t in order)
      + "</nav>")
    for t in order:
        rs = sorted(meetings[t], key=lambda r: int(r["n"]) if str(r["n"]).isdigit() else 0)
        first = min(r["s"] for r in rs)
        a(f"<div class='mh' id='m-{slug(t)}'><h2>{html.escape(t)}</h2><div class='hd'>{len(rs)} races from {when(first)}</div>"
          "<div class='chips'>" + "".join(
              f"<a href='#{anchor(r)}'{' class=\"hb\"' if any(w[0] is r for w in watch) else ''}>R{r['n']} {when(r['s'])}</a>"
              for r in rs) + "</div></div>")
        for r in rs:
            grade = f"Grade {r['g']}" if str(r["g"]).isdigit() else r["g"]
            a(f"<h3 id='{anchor(r)}'>{html.escape(short(t))} Race {r['n']}</h3><div class='hd'>{when(r['s'])} · {r['d']}m · "
              f"{html.escape(grade)} · our market adds to 100% · GRV's to {r['b']:.0%} · {len(r['r'])} runners"
              + (f" · reserve{'s' if len(r['reserves']) > 1 else ''} {html.escape(', '.join(r['reserves']))} left out"
                 if r["reserves"] else "") + "</div>")
            mapped = [x for x in r["r"] if len(x) > 9 and x[9] is not None]
            if mapped:
                fast = min(mapped, key=lambda x: x[9])
                lead = max((x for x in mapped if len(x) > 10 and x[10] is not None), key=lambda x: x[10], default=None)
                bits = [f"fastest early on past splits: {html.escape(fast[0])}. {html.escape(title_case(fast[1]))}"]
                if lead is not None and lead[10] > 0:
                    bits.append(f"leads most often: {html.escape(lead[0])}. {html.escape(title_case(lead[1]))} ({lead[10]:.0%} of its runs)")
                a("<div class='hd'><b>Speed map:</b> " + " · ".join(bits) + ". The fastest early dog leads about 3 races "
                  "in 10 (4 in 10 from box 1), and the leader wins about half (Test 21).</div>")
            for x in r["r"]:
                box, dog, p, grv, rating, tip, bb, last5, fams = x[:9]
                rank, led, inside = (list(x[9:12]) + [None, None, None])[:3]
                lad = ladder(p, race_book(r))
                tags = ""
                if lad and grv and grv >= RATIO / p:
                    tags += "<span class='tag edge'>check TAB</span>"
                elif not lad:
                    tags += "<span class='tag no'>no bet</span>"
                if bb:
                    tags += "<span class='tag bb'>GRV best bet</span>"
                op = op_for(r, dog)
                grv_bits = [f"GRV {money(grv)}"]
                if rating and float(rating) > 0:
                    grv_bits.append(f"rated {float(rating):g}")
                if tip:
                    grv_bits.append(f"tip #{tip}")
                mk = " · ".join([", ".join(grv_bits)] + ([f"TAB opened {money(op[0])}, {money(op[1])} later"] if op else []))
                if lad:
                    lad_txt = "TAB open: " + " · ".join(f"{money(pr)}+ <b>{units(u)}</b>" for m, pr, u in lad)
                    if op:
                        u = stake(p, op[0], race_book(r))
                        lad_txt += (f" · <b>opened {money(op[0])} ({op[0] * p:.2f}x): "
                                    + (f"{units(u)}</b>" if u else "no bet</b>"))
                    reason = f"<span class='lad'>{lad_txt}</span><br>"
                else:
                    reason = (f"<b>No bet:</b> our price {money(1 / p)} is outside the $2-$15 band the rule was tested on. ")
                ups = [f"<span class='up'>{html.escape(fam[k])} +{v}%</span>" for k, v in fams if v > 0][:3]
                dns = [f"<span class='dn'>{html.escape(fam[k])} {v}%</span>" for k, v in fams if v < 0][:3]
                why = " · ".join(ups + dns)
                fair = 1 / grv / r["b"]
                early = []
                if rank is not None:
                    early.append("fastest early in the field on past splits" if rank == 1 else f"{ordinal(rank)} fastest early on past splits")
                if led is not None:
                    early.append(f"led at the first point in {led:.0%} of its last 10")
                if inside:
                    early.append(f"{inside} quicker beginner{'s' if inside > 1 else ''} drawn inside it")
                if early:
                    reason += "<b>Early:</b> " + " · ".join(early) + ".<br>"
                a(f"<div class='r'><div class='px'>{money(1 / p)}<span class='pc'>{p:.0%}</span></div><div>"
                  f"<span class='nm'>{html.escape(box)}. {html.escape(title_case(dog))}</span>{tags}"
                  f"<span class='mk'> · {mk}</span></div><div class='why'>{reason}"
                  f"{'<b>Why:</b> ' + why + '.' if why else ''}<br>"
                  f"last 5: {html.escape(last5) or '-'} · our chance {p:.1%} · GRV's {fair:.1%} with its book taken out</div></div>")
    a("<div class='note'>The reasons are the model's own: each input's push on this dog against the rest of the field, "
      "added up by kind. GRV's values come from Topaz for personal use; this page is private.</div>")
    return "\n".join(out)


if __name__ == "__main__":
    card = json.load(open(sys.argv[1]))
    opens = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    made = datetime.now(MEL).strftime("%-I:%M%p").lower()
    open(sys.argv[2], "w").write(page(card, opens, made, datetime.now(MEL)))
    print(f"wrote {sys.argv[2]}")
