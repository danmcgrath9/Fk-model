"""One page for a whole race day: every meeting's sheet page under one sticky meeting bar, with the day's bets taken at
the open from every meeting in one box at the top (5 Nov 2026, founder: "Create one artifact for all of today please").
    python day_page.py OUT.html "TITLE" NAME=PAGE.html[@2:00pm,2:30pm,...] [NAME=PAGE.html[@TIMES] ...]
The optional @TIMES is each race's jump time in race order (race_times.py): with it the day's game day runs race by race
across every meeting in jump order (founder, 6 Nov 2026: "Why isn't Game Day for both a tab like bets"); without it, by
meeting then race.
Each meeting page is the one meeting.sh / betmatic_html.py / page_takeat.py already built; it is taken as is, its ids and
in-page links prefixed with the meeting so two meetings' "r1" or "gameday" cannot collide, and its own race bar made
non-sticky so only the meeting bar stays at the top. The combined box is copied from each page's own "Our bets at the
open" table (the same figures, one Meeting column added), so the day page can never say something a meeting page
does not. Re-run it whenever a meeting page is rebuilt."""
import html, re, sys

out, title, specs = sys.argv[1], sys.argv[2], sys.argv[3:]
mtgs, times = [], {}
for sp in specs:
    name, path = sp.split("=", 1)
    path, _, tl = path.partition("@")
    slug = re.sub(r"[^a-z0-9]", "", name.lower())
    mtgs.append((name, slug, open(path).read()))
    times[slug] = [t.strip() for t in tl.split(",")] if tl else []


def minutes(t):
    m = re.match(r"(\d{1,2}):(\d{2})\s*([ap]m)", t.lower())
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "pm" else 0)
    return h * 60 + int(m.group(2))

style = re.search(r"<style>.*?</style>", mtgs[0][2], re.S).group(0)   # every page comes from one generator: one stylesheet


def body(s):
    s = re.sub(r"<title>.*?</title>", "", s, count=1, flags=re.S)
    return s.replace(style, "", 1)


def prefix(s, p):
    s = re.sub(r"id='([^']+)'", lambda m: f"id='{p}-{m.group(1)}'", s)
    s = re.sub(r'id="([^"]+)"', lambda m: f'id="{p}-{m.group(1)}"', s)
    s = re.sub(r"href='#([^']+)'", lambda m: f"href='#{p}-{m.group(1)}'", s)
    return re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}-{m.group(1)}"', s)


# the day's bets taken at the open: each page's own box, rows copied, a Meeting cell in front
rows, head, total_u, nbets = [], None, 0.0, 0
for name, slug, s in mtgs:
    box = s[s.find("<!-- betmatic -->"):s.find("<!-- /betmatic -->")]
    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", box, re.S)
    if trs and head is None:
        head = trs[0]
    mine = []
    for tr in trs[1:]:
        if "<b>Total</b>" in tr:
            continue
        cells = re.findall(r"<td[^>]*>.*?</td>", tr, re.S)
        if not cells:
            continue
        u = re.search(r"([\d.]+)u", tr)
        total_u += float(u.group(1)) if u else 0.0
        mine.append(f"<tr>{prefix(''.join(cells), slug)}</tr>")
    # a heading row per meeting instead of a Meeting column: the six columns of the meeting pages fit a 390px phone,
    # a seventh pushed the prices off the side (5 Nov 2026, screenshot)
    rows.append(f"<tr><td colspan='6' style='padding-top:10px'><b><a href='#{slug}'>{html.escape(name)}</a></b>"
                + ("" if mine else " <span class='note'>nothing taken at the open</span>") + "</td></tr>")
    rows += mine; nbets += len(mine)

# the day's game day: every meeting's race blocks (lay_sheet.py's own blocks, ids prefixed) in jump order
blocks, rule = [], ""
for mi, (name, slug, s) in enumerate(mtgs):
    g = s.find("<div class='lb gd' id='gameday'")
    if g < 0:
        continue
    gd = s[g:]
    r_ = re.search(r"<div class='rule'>.*?</div>", gd, re.S)
    if r_ and not rule:
        rule = r_.group(0)
    for b in re.findall(r"<div class='gdr'>.*?</table></div></div>", gd, re.S):
        rn = int(re.search(r"href='#r(\d+)'", b).group(1))
        t = times[slug][rn - 1] if len(times[slug]) >= rn else ""
        b = prefix(b, slug)
        b = re.sub(r"(<h3><a href='#[^']+'>)Race (\d+)(</a>)",
                   lambda m: f"{m.group(1)}{html.escape(name)} R{m.group(2)}{m.group(3)}" + (f" · {html.escape(t)}" if t else ""), b, count=1)
        k = minutes(t)
        blocks.append(((k if k is not None else 10 ** 6), mi, rn, b))
blocks.sort(key=lambda x: (x[0], x[1], x[2]))
gd_all = ("<div class='lb gd' id='gameday-all' style='scroll-margin-top:64px'><h2>Game day, every meeting</h2>" + rule
          + "".join(b for *_, b in blocks) + "</div>") if blocks else ""

H = [f"<title>{html.escape(title)}</title>", style,
     "<style>.dnav{position:sticky;top:env(safe-area-inset-top,0px);z-index:6;background:#fff;display:flex;gap:6px;"
     "overflow-x:auto;padding:8px 0;margin:0 0 12px;border-bottom:2px solid #1b5e20}.dnav a{flex:0 0 auto;min-width:44px;"
     "text-align:center;padding:9px 12px;border-radius:6px;background:#1b5e20;color:#fff;text-decoration:none;"
     "font-weight:700;font-size:14px}.dnav a.top{background:#f0f0f0;color:#1b1b1b}.mtg{border-top:3px solid #1b5e20;"
     "margin-top:28px;padding-top:6px;scroll-margin-top:60px}.mtg .nav{position:static}.mtg h1{font-size:20px}"
     "@media (prefers-color-scheme: dark){.dnav{background:inherit}}</style>",
     f"<h1 id='top'>{html.escape(title)}</h1>",
     "<div class='dnav'><a class='top' href='#top'>Bets</a>"
     + ("<a class='top' href='#gameday-all'>Game day</a>" if blocks else "")
     + "".join(f"<a href='#{slug}'>{html.escape(name)}</a>" for name, slug, _ in mtgs) + "</div>"]
H.append(f"<div class='bets ob'><h2>Our bets at the open, every meeting ({nbets})</h2>")
if nbets:
    hc = re.findall(r"<th[^>]*>.*?</th>", head or "", re.S)
    H.append("<div class='tw'><table><tr>" + "".join(hc) + "</tr>" + "".join(rows)
             + f"<tr><td><b>Total</b></td><td><b>{total_u:.2f}u</b></td><td colspan='4'></td></tr></table></div>")
else:
    H.append("<div class='note'>Nothing taken at the open yet.</div>")
H.append("<div class='note'>Each meeting below has its own race bar, game day, lay book and back book.</div></div>")
H.append(gd_all)
for name, slug, s in mtgs:
    H.append(f"<section class='mtg' id='{slug}'>{prefix(body(s), slug)}</section>")
open(out, "w").write("\n".join(H))
print(f"{out}: {len(mtgs)} meetings, {nbets} bets taken at the open, {total_u:.2f}u")
