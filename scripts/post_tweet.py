"""Post an approved Mercer Tipping tweet: a card image, the main post, then the replies under it (14 Oct 2026, founder:
"after we place the bet we send it out"). Run only by the fk-tweet workflow, whose job waits for the founder's
approval in GitHub before it can read the X keys. Claude prepares the post file; nothing posts without that approval.

    python scripts/post_tweet.py data/live_bets/tweets/NAME.json [--dry-run]

NAME.json: {"text": "main post", "image": "path/to/card.png" (optional), "alt": "image description" (optional),
            "replies": ["reply 1", "reply 2", ...]}
           or "images": [{"path": "card1.png", "alt": "..."}, ...] for up to four cards on the main post (17 Oct 2026)
Keys (environment, from GitHub secrets): X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET (OAuth 1.0a
user context, app permission Read and Write). Refuses a file already posted (NAME.posted.json holds the post IDs), so a
re-run can never post twice. Every failure stops with X's own error message; nothing is retried silently."""
import json, os, sys
import requests


API = "https://api.x.com"


def main():
    fn = sys.argv[1]; dry = "--dry-run" in sys.argv
    done = fn.replace(".json", ".posted.json")
    if os.path.exists(done):
        sys.exit(f"{fn} was already posted ({done}); refusing to post it again")
    p = json.load(open(fn))
    text, replies = p["text"], p.get("replies", [])
    for t in [text] + replies:
        if len(t) > 280:
            sys.exit(f"over 280 characters ({len(t)}): {t[:60]}...")
    images = p.get("images") or ([{"path": p["image"], "alt": p.get("alt")}] if p.get("image") else [])
    if len(images) > 4:
        sys.exit(f"X allows four images on a post, this file has {len(images)}")
    for im in images:
        if not os.path.exists(im["path"]):
            sys.exit(f"image not found: {im['path']}")
    print("POST:", text, "\nIMAGES:", *[im["path"] for im in images], "\nREPLIES:", *replies, sep="\n")
    if dry:
        print("DRY RUN: nothing posted"); return
    from requests_oauthlib import OAuth1
    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    media_ids = []
    for im in images:
        with open(im["path"], "rb") as fh:
            r = requests.post(f"{API}/2/media/upload", auth=auth, files={"media": fh},
                              data={"media_category": "tweet_image"}, timeout=60)
        if r.status_code >= 300:
            sys.exit(f"image upload failed {r.status_code}: {r.text[:500]}")
        mid = (r.json().get("data") or {}).get("id") or r.json().get("media_id_string")
        if not mid:
            sys.exit(f"image upload returned no media id: {r.text[:500]}")
        media_ids.append(str(mid))
        if im.get("alt"):
            requests.post(f"{API}/2/media/metadata", auth=auth, json={"id": str(mid), "metadata": {"alt_text": {"text": im["alt"][:1000]}}}, timeout=30)
    posted = []

    def post(body):
        r = requests.post(f"{API}/2/tweets", auth=auth, json=body, timeout=30)
        if r.status_code >= 300:
            json.dump({"posted": posted, "failed_at": body.get("text", "")[:80], "error": r.text[:500]}, open(done, "w"), indent=1)
            sys.exit(f"post failed {r.status_code}: {r.text[:500]} (posted so far saved to {done})")
        tid = r.json()["data"]["id"]; posted.append(tid); return tid

    body = {"text": text}
    if media_ids:
        body["media"] = {"media_ids": media_ids}
    last = post(body)
    for rep in replies:
        last = post({"text": rep, "reply": {"in_reply_to_tweet_id": last}})
    json.dump({"posted": posted}, open(done, "w"), indent=1)
    print("posted:", posted)


if __name__ == "__main__":
    main()
