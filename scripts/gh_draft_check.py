"""Can the gh CLI on a runner read a DRAFT release by its tag? Read-only.

    python scripts/gh_draft_check.py [TAG]

19 Nov 2026: the history files are on a published release of a public repository, so anyone can
download them, and the Form King licence is personal. A draft release is visible only to people
with push access. Before turning "history" into a draft, this proves the commands every workflow
uses (gh release view and gh release download, by tag) still work on one, using fk-db-backup.
"""
import json, subprocess, sys, tempfile

tag = sys.argv[1] if len(sys.argv) > 1 else "fk-db-backup"
pattern = sys.argv[2] if len(sys.argv) > 2 else "manifest.json"
v = subprocess.run(["gh", "release", "view", tag, "--json", "isDraft,assets"], capture_output=True, text=True)
print("gh release view:", "OK" if v.returncode == 0 else f"FAILED {v.stderr.strip()[:200]}")
if v.returncode == 0:
    d = json.loads(v.stdout)
    print("isDraft:", d.get("isDraft"), "| assets:", len(d.get("assets", [])))
with tempfile.TemporaryDirectory() as t:
    r = subprocess.run(["gh", "release", "download", tag, "--dir", t, "--pattern", pattern], capture_output=True, text=True)
    print("gh release download:", "OK" if r.returncode == 0 else f"FAILED {r.stderr.strip()[:200]}")
