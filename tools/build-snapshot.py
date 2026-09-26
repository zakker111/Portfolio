#!/usr/bin/env python3
"""Build data/published.json — a server-side snapshot of all non-fork repos.
Used by the refresh.yml scheduled workflow; the site falls back to this file
if the live GitHub API check fails or is rate-limited."""
import sys, json, datetime

owner, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src) as f:
    repos = json.load(f)

out = []
for r in repos:
    if r.get("fork"):
        continue
    out.append({
        "name": r["name"],
        "url": f"https://{owner}.github.io/{r['name']}/",
        "html_url": r["html_url"],
        "description": r.get("description") or "",
        "pushed_at": r["pushed_at"],
        "default_branch": r["default_branch"],
    })

snapshot = {
    "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "owner": owner,
    "repos": out,
}
with open(dst, "w") as f:
    json.dump(snapshot, f, indent=2)
print(f"wrote {dst}: {len(out)} repos")
