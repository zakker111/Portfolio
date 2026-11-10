#!/usr/bin/env python3
"""One-shot tweak: make the "checked HH:MM" status honest on a cached visit and
replace unreachable labels with a clear message when the GitHub budget is spent.

Applied by a temporary workflow (index.html is too large for the file API) and
deleted again once live. Asserts on every marker so it can never silently no-op.
"""
import sys

PATH = "index.html"

OLD = """  let sweeping = false;
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
    if (!queue.length) return;"""

NEW = """  let sweeping = false;
  const lastChecked = () => {
    const times = Object.values(cache).map(entry => entry && entry.checkedAt).filter(Boolean);
    if (!times.length) return null;
    return new Date(Math.max(...times)).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  };
  const markUnknown = text => {
    for (const project of projects) {
      const entry = cache[project.dataset.repo];
      if (entry && entry.date) continue;
      const label = labelOf(project);
      if (!label || label.textContent.trim() !== 'Checking update…') continue;
      label.textContent = text;
    }
  };
  async function sweep() {
    if (sweeping || document.hidden) return;
    if (exhausted()) {
      if (status) {
        const mins = Math.max(1, Math.round((limit.reset - now()) / 60000));
        status.textContent = 'github limit reached · retrying in ' + mins + ' min';
      }
      // never leave a card claiming to check something that will not run
      markUnknown('Rate limited — retrying later');
      return;
    }
    const queue = projects.filter(stale);
    if (!queue.length) {
      // nothing is stale, so report the newest cached check instead of leaving
      // the initial "checking …" text on screen forever
      const stamp = lastChecked();
      if (status && stamp) status.textContent = 'checked ' + stamp;
      return;
    }"""

with open(PATH, encoding="utf-8") as f:
    html = f.read()

assert html.count(OLD) == 1, "expected exactly one copy of the sweep block, found %d" % html.count(OLD)
html = html.replace(OLD, NEW)

assert "gh-updates:cache:v1" in html
assert html.count("id=\"check-status\"") == 1
assert "setInterval(refresh" not in html

with open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("tweaked %s: sweep block replaced" % PATH)
