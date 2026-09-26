#!/usr/bin/env python3
"""Build data/published.json — a server-side snapshot of all non-fork repos.
Used by the refresh.yml scheduled workflow; the site falls back to this file
if the live GitHub API check fails or is rate-limited."""
import sys, json, datetime

owner, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]

# Shelve list — keep in sync with SHELF_HIDDEN in index.html.
# Repos listed here are excluded from the snapshot (and thus from the
# site's offline fallback shelf) even while their Pages site is live.
SHELF_HIDDEN = {
    "portfolio", "perkele-cats", "aetheria", "tampere-keikat",
    "roguelike_new_1", "multiplayer_voxel_game", "coding_game-3_newest",
    "roguelike_whit_world", "roguelike_new", "coding_game2", "coding_game1",
    "coding_game", "roguelike", "macros-for-euo", "batsbatsbats_godot",
    "shitty-javascript-html5-game",
}

with open(src) as f:
    repos = json.load(f)

out = []
for r in repos:
    if r.get("fork"):
        continue
    if r["name"].lower() in SHELF_HIDDEN:   # shelved — never snapshot it
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
