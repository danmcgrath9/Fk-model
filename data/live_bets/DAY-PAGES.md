# One page per race day (founder, 6 Nov 2026: "lets do that for all days moving forward")

Every race day gets ONE artifact: the day's bets taken at the open from every meeting (top), a Game day tab running every
meeting's races in jump order, then each meeting's full sheet page under its own tab. Built by
research/form_gbm/day_page.py from the meeting pages (scratchpad pages/<YYYYMMDD><track>-market.html) and race_times.py's
output for the day; rebuilt and republished to the SAME URL every time a meeting page is rebuilt (pricing, 9:30am
re-price, settling). A meeting the rules keep on paper is named so, e.g. "Balnarring (paper)".

    python day_page.py pages/<YYYYMMDD>-day.html "Saturday 7 Nov: Flemington, Geelong" \
        "Flemington=pages/20261107flemington-market.html@times.md" "Geelong=pages/20261107geelong-market.html@times.md"

| Day | Day page | Meeting pages |
|---|---|---|
| Fri 6 Nov | https://claude.ai/artifact/6BKUvbtyb3tEdB1aaQRjSN | Warrnambool W3P9Kqos5UV9vUow9jcG9J, Cranbourne AvAe455u9EcuVh2auYMYYn |
| Sat 7 Nov | https://claude.ai/artifact/6CRFcxkimi3VKvKTDnKfjJ | Flemington PmmAonDNth57w9t6WrLu14, Geelong KxfoC1egzmhSzboJsf7nq3, Balnarring (paper) TSQ99aFGvBQefyZjPV6tX2 |
| Sun 8 Nov | https://claude.ai/artifact/3JXGEaqtWD6BWMHbTypi7p | Ararat TfZ5fyyi5WL5SEdhh2swQ6 |
| Mon 9 Nov | https://claude.ai/artifact/Dq3vc1zPPma8nmtKnceYUu | Hamilton 46dj1Wf9Ff5Y31cdup9yRU |
| Tue 10 Nov | https://claude.ai/artifact/YHGy8d8K3W5ECzCCrbgP8f | Mornington Xr8qgNxZdhraUL9c3w63bY |
| Wed 11 Nov | https://claude.ai/artifact/AaChdeRZH8mSpwcZLGyx7e | Ballarat WXrtczNxaAj1PnW6zrVzb7 |
| Thu 12 Nov | https://claude.ai/artifact/FAxSpXb1m6R7EbuCKKQkiK | Seymour CyoPhaaBWcSATT2gUCnfna |
| Fri 13 Nov | https://claude.ai/artifact/XSphxFyR76aD3KLeNW6NMF | Pakenham, Geelong (on the day page) |
| Sat 14 Nov | https://claude.ai/artifact/AAoLQZosrkFrBLz3NnaUqt | Sandown (on the day page), Dunkeld (paper) AcdT6xxTmHXF4stSx3Vj1z, Yea (paper) VhTRfTD3hoU7wwb9QRZVJP |
| Sun 15 Nov | https://claude.ai/artifact/QkjrfewVVs9hywgkDQ9vAQ | Donald (provisional) SswFCLTk8KfhrtHQFtg8D1, Moe (provisional) C3mZgX1xxMBsjhS2xzHJk8 |
