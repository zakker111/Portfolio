#!/usr/bin/env python3
"""One-shot patch: replace the inline "Updated ..." label script in index.html.

Why this file exists: index.html is ~55 KB, which is too large to push through
the GitHub file API from the agent, so the change is applied by a temporary
workflow that runs this script and commits the result. The script is deleted
again once it has run.

It rewrites only the single <script> block that reads GitHub commit dates. It
asserts on every assumption and exits non-zero if the markup has moved, so a
silent no-op is impossible.
"""
import sys

PATH = "index.html"

NEW_BLOCK = """<script>
(() => {
  const projects = [...document.querySelectorAll('.project[data-repo]')];
  const status = document.getElementById('check-status');
  if (!projects.length) return;

  // ── Request budget ────────────────────────────────────────────────────
  // GitHub's unauthenticated API allows 60 requests per hour per IP, shared
  // by everybody behind that IP. The previous version asked once per card on
  // every page load and re-ran the whole sweep every 5 minutes — about 84
  // requests/hour from a single open tab — with no memory between visits, so
  // dates vanished as soon as the budget ran out. Now a repo is re-checked at
  // most once every 6 hours, answers are cached in localStorage (a reload
  // costs nothing), sweeps only touch repos that are actually stale, and the
  // rate-limit headers are obeyed instead of guessed.
  const CACHE_KEY = 'gh-updates:cache:v1';
  const LIMIT_KEY = 'gh-updates:limit:v1';
  const FRESH_MS = 6 * 60 * 60 * 1000;   // per-repo freshness window
  const SWEEP_MS = 15 * 60 * 1000;       // background sweep cadence
  const GAP_MS = 700;                    // spacing between requests
  const LOW_WATER = 3;                   // stop while this few requests remain

  const read = (key, fallback) => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) { return fallback; }
  };
  const write = (key, value) => {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch (error) { /* private mode or quota — page still works */ }
  };

  const cache = read(CACHE_KEY, null) || {};
  let limit = read(LIMIT_KEY, null) || {remaining: 60, reset: 0};

  const formatDate = value => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Date unavailable';
    return 'Updated ' + date.toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'});
  };
  const labelOf = project => project.querySelector('[data-updated]');
  const showDate = (project, date, sha) => {
    const label = labelOf(project);
    if (!label || !date) return;
    label.innerHTML = '<span class="update-dot"></span>' + formatDate(date);
    label.title = sha
      ? 'Latest repository commit: ' + sha.slice(0,7) + '. Click Source to view it.'
      : 'From the portfolio snapshot that the scheduled workflow refreshes.';
  };
  const now = () => Date.now();
  const exhausted = () => limit.reset > now() && limit.remaining <= LOW_WATER;
  const stale = project => {
    const entry = cache[project.dataset.repo];
    return !entry || !entry.checkedAt || now() - entry.checkedAt > FRESH_MS;
  };

  // Head start from the committed snapshot: same origin, so it costs nothing
  // against the GitHub budget. It only covers repos the workflow keeps, so it
  // supplements the per-repo check rather than replacing it.
  async function prefill() {
    const missing = projects.filter(project => !(cache[project.dataset.repo] || {}).date);
    if (!missing.length) return;
    try {
      const response = await fetch('data/published.json');
      if (!response.ok) return;
      const snapshot = await response.json();
      const rows = Array.isArray(snapshot.repos) ? snapshot.repos : [];
      const byName = new Map(rows.map(row => [String(row.name).toLowerCase(), row]));
      let touched = false;
      for (const project of missing) {
        const row = byName.get(project.dataset.repo.split('/').pop().toLowerCase());
        if (!row || !row.pushed_at) continue;
        cache[project.dataset.repo] = {date: row.pushed_at, sha: '', checkedAt: 0};
        showDate(project, row.pushed_at, '');
        touched = true;
      }
      if (touched) write(CACHE_KEY, cache);
    } catch (error) { /* the snapshot is a bonus, never a requirement */ }
  }

  function paint() {
    for (const project of projects) {
      const entry = cache[project.dataset.repo];
      if (entry && entry.date) showDate(project, entry.date, entry.sha);
    }
  }

  async function check(project) {
    const repo = project.dataset.repo;
    const known = cache[repo] || {};
    try {
      const response = await fetch('https://api.github.com/repos/' + repo + '/commits?per_page=1', {
        headers: { Accept: 'application/vnd.github+json' },
        cache: 'no-store'
      });
      const remainingHeader = response.headers.get('x-ratelimit-remaining');
      const resetHeader = response.headers.get('x-ratelimit-reset');
      if (remainingHeader !== null) {
        const remaining = Number(remainingHeader);
        const reset = Number(resetHeader);
        if (Number.isFinite(remaining)) {
          limit = {remaining, reset: Number.isFinite(reset) ? reset * 1000 : limit.reset};
          write(LIMIT_KEY, limit);
        }
      }
      if (!response.ok) throw new Error('GitHub returned ' + response.status);
      const commits = await response.json();
      if (!Array.isArray(commits) || !commits[0]) throw new Error('No public commit found');
      const sha = commits[0].sha;
      const date = commits[0].commit?.committer?.date || commits[0].commit?.author?.date;
      cache[repo] = {date, sha, checkedAt: now()};
      write(CACHE_KEY, cache);
      project.dataset.latestCommit = sha;
      if (known.sha && known.sha !== sha) {
        const label = labelOf(project);
        if (label) {
          label.classList.add('changed');
          label.innerHTML = '<span class="update-dot"></span>New update detected';
          label.title = 'A new commit was detected. Latest commit: ' + sha.slice(0,7);
          setTimeout(() => {
            label.classList.remove('changed');
            showDate(project, date, sha);
          }, 7000);
        }
      } else {
        showDate(project, date, sha);
      }
    } catch (error) {
      // Never trade a date we already know for a warning: keep showing it and
      // explain the staleness in the tooltip instead.
      if (known.date) {
        showDate(project, known.date, known.sha);
        const label = labelOf(project);
        if (label) label.title = 'GitHub could not be reached just now — this is the last known date.';
      } else {
        const label = labelOf(project);
        if (label) {
          label.textContent = 'Update status unavailable';
          label.title = 'GitHub public API could not be reached. The project link still works.';
        }
      }
    }
  }

  let sweeping = false;
  async function sweep() {
    if (sweeping || document.hidden) return;
    if (exhausted()) {
      if (status) {
        const mins = Math.max(1, Math.round((limit.reset - now()) / 60000));
        status.textContent = 'github limit reached · retrying in ' + mins + ' min';
      }
      return;
    }
    const queue = projects.filter(stale);
    if (!queue.length) return;
    sweeping = true;
    if (status) status.textContent = 'refreshing…';
    for (const project of queue) {
      if (exhausted()) break;
      await check(project);
      await new Promise(resolve => setTimeout(resolve, GAP_MS));
    }
    sweeping = false;
    if (status && !exhausted()) {
      status.textContent = 'checked ' + new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
    }
  }

  paint();
  prefill().then(sweep);
  window.setInterval(sweep, SWEEP_MS);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) sweep(); });
})();
</script>"""

with open(PATH, encoding="utf-8") as f:
    html = f.read()

START = "<script>\n(() => {\n  const projects = [...document.querySelectorAll('.project[data-repo]')];"
END = "})();\n</script>"

start = html.find(START)
assert start != -1, "could not find the inline update-label script (start marker)"
end = html.find(END, start)
assert end != -1, "could not find the end of the inline update-label script"
end += len(END)

old = html[start:end]
assert "check-status" in old, "matched block does not look like the label script"
assert "api.github.com" in old, "matched block does not query the GitHub API"
assert len(old) < 4000, "matched block is unexpectedly large (%d chars)" % len(old)

if old == NEW_BLOCK:
    print("already patched — nothing to do")
    sys.exit(0)

html = html[:start] + NEW_BLOCK + html[end:]

# Guard rails against a half-applied patch.
assert html.count('id="check-status"') == 1
assert "gh-updates:cache:v1" in html
assert "setInterval(refresh" not in html

with open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("patched %s: %d -> %d bytes" % (PATH, len(old), len(NEW_BLOCK)))
