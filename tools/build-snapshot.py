#!/usr/bin/env python3
"""Build data/published.json — a server-side snapshot of all non-fork repos.
Used by the refresh.yml scheduled workflow; the site falls back to this file
if the live GitHub API check fails or is rate-limited.

Also keeps index.html fresh on every run:
- rewrites the <!-- LAST-UPDATED:... --> marker; a tiny inline script turns it
  into a visible "updated N days ago" badge (the day count is recomputed by
  the browser from this stamp, so it stays accurate between workflow runs),
- checks every external link in index.html (GitHub repos/READMEs via the API,
  Pages URLs via HEAD) and injects a machine-managed AUTO-LINKS block with the
  verified links, replacing any dead hand-written ones,
- verifies that the PROJECTS array entries still exist as repos (reported only).
"""
import sys, json, datetime, re, os, urllib.request, urllib.error

# The self-updating "updated N days ago" badge. The visible slot already lives
# in the header (span#lastUpdatedBadge); this one-time bootstrap reads the
# LAST-UPDATED marker and fills it. Idempotent: only written when missing.
STAMP_SNIPPET = """<script>(function(){var m=document.body&&document.body.innerHTML.match(/LAST-UPDATED:([^\\s>-]+)/);if(!m)return;var t=Date.parse(m[1]);if(isNaN(t))return;var d=Math.floor((Date.now()-t)/864e5);var txt=d<=0?'updated today':'updated '+d+' day'+(d===1?'':'s')+' ago';var b=document.getElementById('lastUpdatedBadge');if(b){b.textContent=txt;b.style.display='inline';}})();</script>"""

owner, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
index_path = os.path.join(repo_root, "index.html")

UA = {"User-Agent": "portfolio-refresh-bot", "Accept": "application/vnd.github+json"}
_tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if _tok:
    UA["Authorization"] = "Bearer " + _tok   # Actions token lifts the limit to 5000 req/h


def http_status(url, method="GET"):
    """Return HTTP status code for a URL, or None if unreachable."""
    req = urllib.request.Request(url, method=method, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None

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

now = datetime.datetime.now(datetime.timezone.utc)
# Honor GITHUB_EVENT_HEAD_SHA (the commit that triggered this run) so the
# LAST-UPDATED marker never changes twice in one cycle — that would make
# every refresh push an extra, pointless commit.
ev = os.environ.get("GITHUB_EVENT_HEAD_SHA")
if ev:
    try:
        import subprocess
        head_dt = subprocess.run(["git", "--no-pager", "show", "-s", "--format=%cI", ev],
                                 capture_output=True, text=True, timeout=15).stdout.strip()
        if head_dt:
            dt = datetime.datetime.fromisoformat(head_dt.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            # never stamp the snapshot earlier than its own content
            now = max(now, dt.astimezone(datetime.timezone.utc))
    except Exception:
        pass
snap_json = json.dumps({
    "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "owner": owner,
    "repos": out,
}, indent=2)
with open(dst, "w") as f:
    f.write(snap_json)
print(f"wrote {dst}: {len(out)} repos")

# ── index.html maintenance ────────────────────────────────────────────────
try:
    with open(index_path, encoding="utf-8") as f:
        html = f.read()
except FileNotFoundError:
    html = None
    print("index.html not found — skipping page maintenance")

if html is not None:
    original = html
    report = []

    # 1. LAST-UPDATED marker + visible "updated N days ago" badge
    iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if re.search(r"<!--\s*LAST-UPDATED:", html):
        html = re.sub(r"<!--\s*LAST-UPDATED:[^>]*-->", f"<!-- LAST-UPDATED:{iso} -->", html)
    else:
        html = html.replace("<div id=\"progress\"></div>",
                            f"<div id=\"progress\"></div>\n<!-- LAST-UPDATED:{iso} -->", 1)
    # inject the badge markup once (idempotent — no churn on later runs)
    if 'id="lastUpdatedBadge"' not in html:
        html = re.sub(r"(<!--\s*LAST-UPDATED:[^>]*-->)",
                      lambda m: m.group(1) + "\n" + STAMP_SNIPPET, html, count=1)

    # 2. collect external links from the page (static hrefs + PROJECTS array)
    body = re.sub(r"<head>.*?</head>", "", html, flags=re.S)   # skip <link> preconnect/font CSS
    links = set(re.findall(r'href="(https://[^"]+)"', body))
    # only real entries in the PROJECTS array count — not example code inside comments
    marr = re.search(r"const\s+PROJECTS\s*=\s*\[(.*?)\n\];", html, re.S)
    # strip /* ... */ blocks and // line comments FIRST — the docs contain a
    # commented-out EXAMPLE entry whose fake repo must never be link-checked.
    arr = re.sub(r"/\*.*?\*/|//[^\n]*", "", marr.group(1)) if marr else ""
    arr_entries = [e for e in re.split(r"\n\s*\{", "\n{" + arr) if "slug:" in e]
    arr_clean = "\n".join(arr_entries)
    arr_repos = re.findall(r"repo:\s*'([^']+)'", arr_clean)
    arr_lives = re.findall(r"live:\s*'(https://[^']+)'", arr_clean)
    for repo in arr_repos:
        links.add("https://github.com/" + repo.strip("/"))
        links.add("https://github.com/" + repo.strip("/") + "/blob/main/README.md")
    for live in arr_lives:
        links.add(live)
    api_repos = {r["html_url"]: r for r in repos if not r.get("fork")}
    by_name = {r["name"].lower(): r for r in repos if not r.get("fork")}

    def verify(url):
        """(alive, reason). GitHub URLs use the API snapshot when possible."""
        m = re.match(r"https://github\.com/([^/]+)/([^/#?]+)(?:/(.*))?$", url)
        if m:
            key = m[1] + "/" + m[2]
            tail = m[3] or ""
            info = api_repos.get(key)
            if info is None:                       # not our repo (or deleted) → API call
                st = http_status("https://api.github.com/repos/" + key)
                if st != 200:
                    return False, "repo missing (API %s)" % st
                return True, ""
            if not tail:
                return True, ""
            path = re.sub(r"^(?:blob|tree)/[^/]+/", "", tail)
            q = urllib.request.Request(
                "https://api.github.com/repos/%s/contents/%s?ref=%s"
                % (key, path, info.get("default_branch", "main")),
                method="HEAD", headers=UA)
            try:
                urllib.request.urlopen(q, timeout=20)
                return True, ""
            except urllib.error.HTTPError as e:
                if e.code in (404, 451):
                    return False, "path missing (%d)" % e.code
                return True, ""                    # other errors: don't judge
            except Exception:
                return True, ""                    # unreachable: leave alone
        if url.endswith(".github.io/") or ".github.io/" in url:
            st = http_status(url, method="HEAD")
            if st in (404, 410):
                return False, "pages 404"
            return True, ""                        # 2xx or unknown → fine
        st = http_status(url, method="HEAD")
        if st is None:
            st = http_status(url)
        if st is not None and st >= 400:
            return False, "http %d" % st
        return True, ""

    dead = {}
    for u in sorted(links):
        ok, why = verify(u)
        if not ok:
            dead[u] = why
            report.append("DEAD  %s (%s)" % (u, why))
        else:
            report.append("ok    %s" % u)

    # 3. PROJECTS entries whose repo no longer exists → warn only (human edits)
    for slug, rep in re.findall(r"slug:\s*'([^']+)'.*?repo:\s*'([^']+)'", arr_clean, re.S):
        name = rep.split("/")[-1].lower()
        if name not in by_name and http_status("https://api.github.com/repos/" + rep) != 200:
            report.append("WARN  PROJECTS entry '%s' → repo %s not found" % (slug, rep))

    # 4. machine-managed AUTO-LINKS block: verified pages per project repo
    proj_repos = [r for r in arr_repos if r.lower().startswith(owner.lower() + "/")]
    auto_lines = ["<!-- AUTO-LINKS-BEGIN (machine-managed by tools/build-snapshot.py — do not edit) -->"]
    for rep in dict.fromkeys(proj_repos):          # dedupe, keep order
        name = rep.split("/")[-1]
        r = by_name.get(name.lower())
        if not r:
            continue
        pages = "https://%s.github.io/%s/" % (owner, name)
        if pages in dead:
            continue                               # dead link never injected
        auto_lines.append('<p><a href="%s">%s ↗</a></p>' % (pages, name))
        auto_lines.append('<p><a href="%s">source · %s ↗</a></p>' % (r["html_url"], rep))
    auto_lines.append("<!-- AUTO-LINKS-END -->")
    block = "\n        ".join(auto_lines)
    begin, end = "<!-- AUTO-LINKS-BEGIN", "<!-- AUTO-LINKS-END -->"
    if begin in html and end in html:
        html = re.sub(re.escape(begin) + r".*?" + re.escape(end), block, html, flags=re.S)
    else:
        anchor = '<div id="staticProjects"'
        pos = html.find(anchor)
        if pos != -1:
            close = html.find("</div>", pos)
            html = html[:close + len("</div>")] + "\n      " + block + html[close + len("</div>"):]

    # 5. drop dead hand-written links from the noscript static list
    for u, why in dead.items():
        pattern = re.compile(r'[ \t]*<p><a href="%s">.*?</a></p>\n' % re.escape(u))
        html, n = pattern.subn("", html)
        if n:
            report.append("REMOVED dead link from page: %s" % u)

    if html != original:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("index.html updated")
    else:
        print("index.html unchanged")
    with open(os.path.join(repo_root, "data", "link-report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print("link report: %d checked, %d dead" % (len(links), len(dead)))
