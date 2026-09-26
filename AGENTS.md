# AGENTS.md — guide for AI agents working on this site

Single-file static portfolio on GitHub Pages. No build step, no dependencies.

## How to add a project (the easy way)

Edit `index.html` → find the `PROJECTS` array near the top of the `<script>`
at the bottom of the file. Copy one entry and change the fields:

| field   | meaning                                                        |
|---------|----------------------------------------------------------------|
| slug    | unique id; card anchor becomes `#p-<slug>`                     |
| title   | project name                                                   |
| kind    | small label, e.g. `"Game"`, `"Web app"`                        |
| blurb   | one sentence description                                       |
| repo    | `"owner/name"` on GitHub (drives source link + live status)    |
| live    | hosted URL, or `""` if none                                    |
| acc     | accent color, e.g. `'#7dedc3'`                                 |
| tile    | animated sketch: `aetheria` \| `roguelike` \| `voxel` \| `keikat` \| `none` |
| note    | caption under the sketch (optional)                            |
| hidden  | set `true` to keep the entry but hide the card                 |

The card HTML, nav index, "Project NN" numbering and hero counters are all
generated from this array — never duplicate them by hand. (The old footer with
its quick links was removed; there is no `#footerLinks` anymore.)

Rules:
- To add a new animated sketch, write a `makeX(canvas)` function returning
  `(t, dt) => {...}` and register it in the `MAKERS` map; then use `tile:'x'`.
- Colors/fonts live only in the `:root` block at the top of `<style>`.
- Hand-written `<article class="project">` blocks in `#projectList` still
  work (they take priority over a matching array entry), but prefer the array.
- The page must stay usable with JavaScript off: keep the `<noscript>`
  fallback list in sync when projects change.
- Never introduce a build step, bundler, framework or external JS dependency.

## Deploy

Pushing to `main` runs `.github/workflows/pages.yml` (static upload, no npm).

## Always-updated machinery

1. **Browser side (index.html):** the published-shelf scan re-runs on every
   page load, every 5 minutes while open, and whenever the tab regains
   focus. If the live GitHub API check fails (offline/rate-limit), it falls
   back to `data/published.json`.
2. **Server side (.github/workflows/refresh.yml):** a scheduled workflow runs
   every 6 hours (also manual-dispatch) and regenerates `data/published.json`
   via `tools/build-snapshot.py`, committing it to `main` only when changed.
   That push then triggers the Pages deploy automatically.

Rules:
- `data/published.json` is machine-generated — never hand-edit it.
- `tools/build-snapshot.py` takes args: `<owner> <input-repos.json> <output.json>`.
- The intermediate `data/repos.json` is gitignored; don't commit it.

## Live status checks (index.html)
Two independent checkers run in the browser on every page load:
1. Per-project cards — repo/pages/readme/last-push via `api.github.com/repos/<owner>/<repo>`.
2. Account sweep — lists ALL public repos of the owner (`/users/<owner>/repos`), HEAD-checks each one's Pages URL, and renders every published-and-answering site as a clickable card in the `#published` shelf (newest first; featured projects reuse their accent color + ★; each card shows the repo description). Tally shows in hero stat `#statAll`. Owner is auto-detected from the github.io hostname (fallback: zakker111). Unpublished repos (404) are skipped silently; published-but-erroring ones go to the console + `#statAll` tooltip. The shelf is fully automatic — never hand-add cards to `#pubGrid`; publishing a new Pages repo makes it appear by itself.
Both degrade gracefully: rate-limit/offline → snapshot fallback → dashes + "checks paused", never an error dialog. The sweep re-runs every 5 minutes while the tab is open and whenever the tab regains focus (generation-guarded so stale runs never overwrite fresh results). Note: unauthenticated api.github.com allows ~60 requests/hour per IP; a full sweep costs ~2 calls per repo. Keep the number of featured cards modest.
Contact link: removed — the footer `#contactLink` and the `CONTACT_EMAIL` constant were deleted along with the footer. (If a contact link is ever re-added, prefer the public GitHub profile email over hard-coding a mailto.)
