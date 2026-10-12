"""Opening prices from the fifth field of a prices file (12 Oct 2026, founder: "record them ... the opening price").
Two opens are recorded per runner, because they are different markets:
    fk_open 8.50    Form King's average opening price (the open every backtest and the blend were fitted on)
    tab_open 9.00   the TAB's opening price, read off the founder's screenshot (TAB goes up first and runs a bit higher)
The field may carry either or both, in any order: "fk_open 8.50 tab_open 9.00". A bare number is read as fk_open,
so every prices file written before this change reads exactly as it did.
The open that DRIVES the blend and the value-at-open rule is fk_open, because that is the tested one; the TAB open is
used only when Form King has none yet, and is then reported as the open used, never silently."""
import re

def parse_opens(field):
    """-> (fk_open or None, tab_open or None). Values at or under 1.0 are not prices and are dropped."""
    field = (field or "").split("#")[0]
    get = lambda lab: (lambda m: float(m.group(1)) if m else None)(re.search(lab + r"\s+([\d.]+)", field))
    fk, tab = get("fk_open"), get("tab_open")
    if fk is None and tab is None:
        m = re.fullmatch(r"\s*([\d.]+)\s*", field)
        fk = float(m.group(1)) if m else None
    ok = lambda v: v if v is not None and v > 1 else None
    return ok(fk), ok(tab)

def open_used(field):
    """The open the rules run on: Form King's, else the TAB's. -> (price or None, 'fk' | 'tab' | None)."""
    fk, tab = parse_opens(field)
    return (fk, "fk") if fk else (tab, "tab") if tab else (None, None)

if __name__ == "__main__":
    for f in ["fk_open 8.50", "8.5", "fk_open 8.50 tab_open 9.00", "tab_open 9", "", "SCR", "tab_open 9.00 fk_open 8.50"]:
        print(repr(f), parse_opens(f), open_used(f))
