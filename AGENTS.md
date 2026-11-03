# AGENTS.md — guide for AI agents working on this site

Single-file static portfolio on GitHub Pages. No build step, no dependencies,
no frameworks — everything (markup, CSS, inline SVG animations, JS) lives in
`index.html`.

## Page structure (as it actually is)

- `index.html` contains **hand-written `<article class="project">` cards**
  inside the `#projects` section, numbered 01…NN in document order. There is
  **no `PROJECTS` array and no canvas `MAKERS` system** — earlier revisions had
  them; they were removed when the page was simplified. Don't re-add machinery
  unless explicitly asked.
- Each card: number + title + kind label + blurb + two buttons (live link ↗ /
  GitHub source ↗) + an **inline SVG preview** animated purely with CSS classes
  (`svg .slot`, `.bob`, `.pulse`, `.blink`, `.walk`, `.spin`, `.slow`, …) whose
  keyframes are defined once in the `<style>` block.
- Card anchors: `id="p-<slug>"` (e.g. `#p-pick-one`). Nav/hero anchors used:
  `#top`, `#projects`. Keep these ids unique.
- Entrance stagger: `.project:nth-child(N){animation-delay:…}` entries in the
  CSS — add one whenever you add a card so the cascade stays in sync.
- Live "Updated …" labels: each GitHub-backed card has
  `<span class="updated" data-updated data-repo="owner/name">Checking update…</span>`.
  One small inline `<script>` at the bottom queries
  `api.github.com/repos/<owner>/<repo>` per card, formats the push date, and
  sets `#check-status` ("checked HH:MM" / "Update status unavailable"). It
  degrades gracefully offline — never replace that with anything that can
  throw uncaught errors.
- **External apps without a GitHub repo** (e.g. Pick One, project 07, deployed
  on Cloudflare Workers): give the footer span NO `data-updated` attribute and
  set a static dim caption instead (e.g. "Deployed on Cloudflare Workers"), so
  the checker skips it. Give such cards a distinct accent via
  `style="--accent:#…"`.
- K-18 styling: `.k18-frame` (glowing corners `.k18-corner` + `.scanline`) and
  `.k18-badge` exist solely for the Pick One card. Reuse them only for other
  age-restricted projects; keep the badge visible on the card and the preview.

## Adding a project

Copy an existing `<article class="project">` block and edit: number, title,
kind, blurb, button `href`s, `id="p-<slug>"`, preview SVG, optional accent.
Then bump the `nth-child` delay list. Verify with the checks below before
committing.

## Rules

- Colors/fonts live only in the `:root` block at the top of `<style>`.
- Never introduce a build step, bundler, framework or external JS/CSS
  dependency. Fonts must stay system stacks or self-hosted; no CDN scripts.
- No horizontal overflow at 320px viewport width (the hero headline uses
  `clamp(min(9vw,46px),9vw,100px)` + `overflow-wrap:break-word` for this).
- Respect `prefers-reduced-motion` (already handled globally by a media query
  that squashes all animation durations — don't remove it).
- Favicon is an inline SVG data URI in `<head>` — keep it, otherwise browsers
  log a `/favicon.ico` 404.

## Deploy & automation

- Pushing to `main` runs `.github/workflows/pages.yml` (static upload → GitHub
  Pages at https://zakker111.github.io/portfolio/).
- `.github/workflows/refresh.yml` (Mon/Thu + every 6h + manual dispatch) runs
  `tools/build-snapshot.py <owner> data/repos.json data/published.json`:
  regenerates the repo snapshot and writes `data/link-report.txt`. Its older
  page-maintenance steps (LAST-UPDATED stamp, AUTO-LINKS block, PROJECTS-array
  link parsing) target markup this page no longer has and are skipped
  harmlessly — the script never rewrites `index.html` anymore. Don't hand-edit
  `data/published.json`; `data/repos.json` is gitignored intermediate state.

## Verification checklist (run before pushing)

1. `node --check` on the extracted inline `<script>`.
2. HTML parse: balanced tags, unique ids, every `#anchor` resolves.
3. Headless browser at 320/390/760/1280px: zero console errors, no horizontal
   scroll, all `[data-updated]` labels resolve to real dates (or degrade
   cleanly when the API is blocked).
4. All external links return HTTP 200.
