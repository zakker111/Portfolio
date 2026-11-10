#!/usr/bin/env python3
"""One-shot patch: document the new deploy rules in README.md.

The README is large enough that the file API rejects pushing it whole, so a
temporary workflow runs this script and commits the result. It asserts on every
marker, so a moved section fails the run instead of silently changing nothing.
Deleted again once the change is live.
"""
PATH = "README.md"

OLD_1 = """## Automatic deployment

Every push to `main` triggers the workflow. `workflow_dispatch` also allows a manual deployment from the Actions tab."""

NEW_1 = """## Automatic deployment

Pushing to `main` deploys the site — but only when a file that makes up the site
changes. `pages.yml` is path-filtered to `index.html`, `assets/**`,
`og-image.png`, `og-image.svg`, `robots.txt`, `.nojekyll` and the workflow
itself, so a commit that only touches `data/`, `tools/` or the docs never
rebuilds the page. `workflow_dispatch` also allows a manual deployment from the
Actions tab.

The scheduled refresh obeys the same rule. A commit pushed with `GITHUB_TOKEN`
cannot start `pages.yml` on its own, so `refresh.yml` dispatches it explicitly —
and only when the commit it just made touched one of the site files above.
Deploys are therefore tied to real page changes, not to the calendar."""

OLD_2 = """4. commits & pushes back to `main` only when something changed — which then
   triggers the Pages deploy automatically."""

NEW_2 = """4. commits & pushes back to `main` only when something actually changed: the
   snapshot's `updated` stamp is kept from the previous run when the repo list is
   identical, so a run where nothing happened produces no commit at all,
5. and never redeploys the page for a data-only commit — the site is rebuilt only
   when a site file (`index.html`, `assets/**`, `og-image.*`, `robots.txt`,
   `.nojekyll`) is part of the change."""

with open(PATH, encoding="utf-8") as handle:
    text = handle.read()

for old, new, label in ((OLD_1, NEW_1, "Automatic deployment"), (OLD_2, NEW_2, "refresh list")):
    found = text.count(old)
    assert found == 1, "expected exactly one %s block, found %d" % (label, found)
    text = text.replace(old, new)

# Integrity guards: the edit must not disturb anything else.
assert "path-filtered to `index.html`" in text
assert "produces no commit at all" in text
assert "triggers the workflow" not in text
assert text.count("```") == 2
byte_length = len(text.encode("utf-8"))
assert byte_length == 9114, "unexpected size after patch: %d bytes (expected 9114)" % byte_length

with open(PATH, "w", encoding="utf-8") as handle:
    handle.write(text)

print("patched README.md -> %d bytes" % byte_length)
