"""Tonight's card as a race page, in the shape of the gallops pages (5 Nov 2026, founder: "send me an artifact like
this", the Kyneton page): the paper bets on top, the races as tabs, one row per dog with our price, the market
line and the reasons the model gives.

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


def window(p: float):
    need = 1.5 / p
    lo = max(8.0, need)
    return (lo, 13.0) if lo <= 13.0 else None


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


def page(card: dict, opens: dict, made: str) -> str:
    card = boxed(card)
    fam = card["fam"]
    races = card["races"]
    track = ", ".join(card["tracks"]) or "No track"
    day = datetime.fromisoformat(card["day"]).strftime("%a %-d %b")
    paper = []
    for r in races:
        for x in r["r"]:
            w = window(x[2])
            if w and w[0] <= x[3] <= w[1]:
                paper.append((r, x, w))
    elsewhere = [e for e in card["edges"] if not any(t in e[0] for t in card["tracks"])]
    out = []
    a = out.append
    a(f"<title>{html.escape(track)} {day}, prices {made}</title>")
    a('<meta name="claude:viewport-fit-sides" content="cover">')
    a("""<style>
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
.bets td,.bets th{padding:6px 6px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.bets td:first-child,.bets th:first-child{text-align:left}
.bets th{font-size:12px;color:var(--mute);font-weight:600}
.bets a{color:var(--fg)}
.note{font-size:12.5px;color:var(--mute);margin-top:8px}
</style>""")
    a(f"<h1>{html.escape(track)} {day}, prices {made}</h1>")
    a(f"<div class='sub'>Our model: fitted this morning on {card['fit']:,} Victorian races, {card['rounds']:,} rounds, with "
      "GRV's preview and tips and the ratings upgrades (Tests 15 to 20). Melbourne time. Nothing here has been bet.</div>")
    # bets box
    a("<div class='bets' id='bets'><h2>Paper bets at the open ({})</h2><div class='tw'><table>".format(len(paper)))
    a("<tr><th>Dog</th><th>Our price</th><th>Take at</th><th>GRV price</th><th>TAB open</th></tr>")
    for r, x, w in paper:
        op = opens.get(f"{r['n']}|{x[1].upper()}")
        a(f"<tr><td><a href='#r{r['n']}'>R{r['n']}</a> {html.escape(title_case(x[1]))}</td><td><b>{money(1 / x[2])}</b></td>"
          f"<td>{money(w[0])}-$13</td><td>{money(x[3])}</td><td>{money(op[0]) if op else '-'}</td></tr>")
    if not paper:
        a("<tr><td colspan='5' style='text-align:left'>No dog at this meeting meets the rule tonight.</td></tr>")
    a("</table></div><div class='note'>The rule is Test 12's: a bet when the price is at least 50% over our price and "
      "between $8 and $13. It made money at GRV's SP in 26 of 30 months walk-forward and lost at Betfair's price. These "
      "are paper: nothing goes to BetMatic without your OK, and the open price is the one that counts.</div>")
    if elsewhere:
        a("<div class='note'><b>Elsewhere on the card:</b> " + "; ".join(
            f"{html.escape(e[0])} R{e[1]} {html.escape(title_case(e[3]))} (ours {money(1 / e[4])}, GRV {money(e[5])})"
            for e in elsewhere) + ".</div>")
    a("</div>")
    # nav
    a("<nav class='nav'><a href='#bets' class='hb'>Bets</a>" + "".join(
        f"<a href='#r{r['n']}'{' class=\"hb\"' if any(p[0] is r for p in paper) else ''}>R{r['n']}</a>" for r in races) + "</nav>")
    for r in races:
        grade = f"Grade {r['g']}" if str(r["g"]).isdigit() else r["g"]
        a(f"<h2 id='r{r['n']}'>Race {r['n']}</h2><div class='hd'>{when(r['s'])} · {r['d']}m · {html.escape(grade)} · "
          f"our market adds to 100% · GRV's to {r['b']:.0%} · {len(r['r'])} runners"
          + (f" · reserve{'s' if len(r['reserves']) > 1 else ''} {html.escape(', '.join(r['reserves']))} left out"
             if r["reserves"] else "") + "</div>")
        for x in r["r"]:
            box, name, p, grv, rating, tip, bb, last5, fams = x
            w = window(p)
            tags = ""
            if w and w[0] <= grv <= w[1]:
                tags += "<span class='tag edge'>EDGE (paper)</span>"
            elif not w:
                tags += "<span class='tag no'>no bet</span>"
            if bb:
                tags += "<span class='tag bb'>GRV best bet</span>"
            op = opens.get(f"{r['n']}|{name.upper()}")
            grv_bits = [f"GRV {money(grv)}"]
            if rating and float(rating) > 0:
                grv_bits.append(f"rated {float(rating):g}")
            if tip:
                grv_bits.append(f"tip #{tip}")
            mk = " · ".join([", ".join(grv_bits)] + ([f"TAB opened {money(op[0])}, {money(op[1])} at 7:47am"] if op else [])
                            + [f"take at {money(1.5 / p)} or better"])
            reason = ""
            if not w:
                reason = (f"<b>No bet:</b> our price over $8.67, so a 50% edge needs more than $13, outside the band "
                          "the rule was tested on. ")
            ups = [f"<span class='up'>{html.escape(fam[k])} +{v}%</span>" for k, v in fams if v > 0][:3]
            dns = [f"<span class='dn'>{html.escape(fam[k])} {v}%</span>" for k, v in fams if v < 0][:3]
            why = " · ".join(ups + dns)
            fair = 1 / grv / r["b"]
            a(f"<div class='r'><div class='px'>{money(1 / p)}<span class='pc'>{p:.0%}</span></div><div>"
              f"<span class='nm'>{html.escape(box)}. {html.escape(title_case(name))}</span>{tags}"
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
    open(sys.argv[2], "w").write(page(card, opens, made))
    print(f"wrote {sys.argv[2]}")
