# AGENTS.md — rules for this repository

Portfolio site of **zakker111**, served by GitHub Pages (legacy build, source `main:/`).

Live: https://zakker111.github.io/Portfolio/

## The strict rule: `index.html` is the projects page and must stay as it is

`index.html` is **standalone and frozen**. It is the whole site as designed; it must keep
looking and behaving exactly as it does today.

The canonical, approved version is commit **`a8a8354`** (after the approved move of the Tools
section to its own `tools.html` page). At any time:

```bash
git diff a8a8354 -- index.html    # must be empty, or only the change explicitly requested
```

must show nothing except changes the user asked for **in that same request**. All approved
changes to date (footer link, card look, Tools moved to `tools.html`, Source links removed) are
already folded into baseline `a8a8354`.

### Never do this to `index.html`

- Do not restructure it: no reordering of the hero or `#projects`, no new sections.
  (`index.html` now holds one section, `#projects`; the Tools cards live in `tools.html`.)
- Do not restyle it: do not touch the inline `<style>` block, the CSS variables, the
  `.card-grid` breakpoints (1 col ≤760px, 2 cols 761–1079px, 3 cols ≥1080px), the type scale,
  the colours or the spacing — with the single exception of the approved card look described
  below, which must stay exactly as it is.
- Do not edit, replace or remove the 9 project cards: their order, `--accent` colours, preview
  SVGs, numbers, descriptions, tags and their primary action links stay byte-identical.
  (The secondary `Source ↗` GitHub links were removed on request; GitHub links remain on
  `links.html`.)
- Do not change the header nav (`Projects` → `#projects`, `Tools` → `tools.html`) or add nav
  items on your own.
- Do not change the hero copy, the section headers, the footer text or the cookie banner.
- Do not re-add a link or page that was removed unless the user asks for it again.
- Do not reformat, "tidy" or prettify the file. It is one long line-per-block by design.

### The only allowed edits to `index.html`

Explicitly requested, one at a time:

- one new small link pointing at an extra page (e.g. the footer link `Other stuff ↗` →
  `about.html`), written with the existing footer/affordance markup and no new CSS; or
- the single change the user just asked for, after which the baseline in this file moves.

Cards, copy, nav, CSS and the rest of the page are otherwise frozen. If a request seems to need
more than that on `index.html`, stop and ask.

### Approved card look (do not change)

The project and tool cards render as **big cards**: preview block on top, then the number, title,
description, tags and buttons underneath, inside a 1px bordered panel. One card per row on phones,
two on tablet, three on desktop, 26 px between rows, accent-coloured border on hover. This is
folded into the original rules (not a trailing override block):

```css
.card-grid{display:grid;grid-template-columns:1fr;gap:26px 32px;width:100%}
.project{--accent:var(--mint);display:grid;grid-template-columns:minmax(0,1fr);gap:0;align-items:stretch;padding:0;border:1px solid var(--line);background:var(--panel);overflow:hidden;animation:appear .7s both;transition:border-color .25s}
.preview{min-width:0;border:0;border-bottom:1px solid var(--line);background:var(--panel);transition:border-color .25s}
.project:hover{border-color:var(--accent)}
.project-info{padding:22px 20px 24px}
```

## Extra pages

- `about.html`, `tools.html`, `links.html` all share the same header nav:
  `Projects` (`./#projects`) · `Tools` (`tools.html`) · `About` · `Links`.
- Each ends with a `.page-back` "← Back to the projects" link and the shared `.site-foot`.
- `404.html` follows the same shell but must use **absolute** `/Portfolio/…` paths for its
  stylesheet and links (GitHub Pages serves it at the missing URL, so relative paths break on
  deeper paths), sets `<meta name="robots" content="noindex">`, and its link list mirrors
  `links.html` — update both when a link is added or removed.

## Extra content lives on separate pages

New material (about me, languages, tools, notes, anything else) goes into its **own page**
next to `index.html`, never into `index.html`:

- reuse `assets/site.css` (the stylesheet extracted from `index.html`, plus the shared
  `.site-foot` and `.page-back` helpers) so the style is identical;
- use the existing components: `section.hero` + `.kicker` + `h1` + `p.intro` + `.hero-link`,
  `.section-head`, `.card-grid` > `article.project.tool` with `.preview`, `.monogram`,
  `.project-info`, `.number`, `.tags`, `.tag`, `.actions`, `.btn primary`;
- give each page `<title>`, `meta description`, `link rel="canonical"`, the shared favicon and the
  same Open Graph / Twitter block as `index.html` (per-page `og:title`/`og:description`/`og:url`,
  shared `og-image.png`), so shared links get a preview;
- link it from `index.html` with **one** small link, only when asked.

## Data: update labels come from the CI snapshot

The "Updated …" labels under each project read `data/published.json`, refreshed by
`.github/workflows/refresh-snapshot.yml` (generator: `.github/scripts/build-snapshot.mjs`)
on a six-hour schedule or by hand. It commits only when a project's latest commit changes;
`generated_at` is the time the data last changed, so the page's snapshot timestamp stays
honest instead of advancing on every check. Portfolio pushes and pull requests only run the three
guard steps — the honest-copy check, the 404 redirect map and the check that proves those two can
fail — and never commit a snapshot (on a push that would start a second Pages build and cancel
the build for the push).

- The page must never call `api.github.com` from the browser.
- Do not remove the `.github/` workflow or script, and do not add a client-side GitHub fetch.

## CI: the frozen-index guard, the honest-copy check, the snapshot job and the live smoke test

Two workflows run on a six-hour schedule (offset from each other); pushes run the guards, and pull
requests run the copy and 404 checks too. A fourth workflow turns a red guard run into a GitHub
issue, so a failure is not missed between deploys. None of them may be deleted:

- **`refresh-snapshot.yml` — snapshot.** Runs on the schedule, by hand, and on pushes to `main`
  and pull requests that touch the HTML or its own files. Only scheduled/manual runs update
  `data/published.json`; pushes and pull requests only run the tests, so a push never produces a
  snapshot commit that would start a second Pages build. Those steps are the honest-copy check,
  the 404 redirect map and `.github/scripts/guard-selftest.mjs`, so hand-built copy fails the
  branch's own run before it lands on `main`, not only after the deploy has gone live. The
  self-test is what keeps the other two honest: it runs the copy check against a throwaway fixture
  page saying "built by hand" (must exit 1, and exit 0 on clean copy) and the 404 test against a
  fixture page whose redirect map handles a near-miss URL (must pass) and one with the map broken
  (must fail). Fixtures are built in the system temp directory, so bad copy never enters the
  repository and nothing bad is ever deployed.
- **`live-smoke.yml` — live smoke test and honest-copy check.** Runs after every **successful
  GitHub Pages deployment** (so a broken deploy is caught immediately) and every six hours, plus
  by hand. Its `smoke` job checks the live site at https://zakker111.github.io/Portfolio/ — status
  and `<title>` for each page, the redirects for near-miss URLs, and that an unknown URL really
  404s. A running check is never cancelled, so the deployment it is testing stays verified. Its
  `copy` job runs alongside it and fails the same run when hand-built copy reappears on any page:
  `about.html` says most projects are **vibe coded**, and that claim has to stay true. The banned
  phrasings ("by hand", "hand-built", "from scratch", "built by me", "every line of code", …)
  live in `.github/scripts/check-honest-copy.mjs`; close a gap by adding a phrasing there, never
  by wording a page around it.
- **`index-frozen.yml` — frozen `index.html` guard.** Runs on every push, on every pull request
  and by hand. It fails when `git diff a8a8354 -- index.html` is non-empty, so the freezing rule
  above is enforced by CI rather than remembered. It only reads the repository; it never
  rewrites the page.
- **`guard-alert.yml` — failed-guard issue.** Runs after `refresh-snapshot.yml`, `index-frozen.yml`
  or `live-smoke.yml` finishes **red**, and opens the single **`CI guard failed`** issue — or
  comments on the one already open, one comment per failure — naming the failed guard, run, commit
  and step. That is how a red guard run on a push or pull request between two deploys gets noticed;
  a second issue is never opened. It reports only guard failures, so the live-smoke `smoke` job and
  the snapshot job are not reported, and it writes nothing but that issue. Dispatching it by hand
  with a failed run's id checks the alert itself without breaking a guard; close the issue once the
  guards are green again.

`index.html` stays frozen throughout: CI only reads the site and refreshes
`data/published.json`, and no workflow or script may rewrite, reformat or "fix" the pages.

## Files

| Path | Rule |
| --- | --- |
| `index.html` | the projects page — frozen, see above |
| `about.html` | extra page ("Other stuff"): bio, languages and other links (tools moved to `tools.html`) |
| `tools.html` | extra page: the 3 tools (Qwen, Freebuff, Google AI Studio), moved out of `index.html` |
| `links.html` | extra page: every site/project/tool/language/profile link in one list |
| `404.html` | extra page served by GitHub Pages for any missing URL: branded hero, client-side search over the links, cards back to the projects. Not in the sitemap, `noindex`, no canonical |
| `assets/site.css` | shared stylesheet copied from `index.html` + `.site-foot`/`.page-back`; keep in sync when the homepage style legitimately changes |
| `og-image.png` | 1200×630 social card |
| `robots.txt`, `sitemap.xml` | crawling; the sitemap lists all four indexed pages (homepage + `tools`/`about`/`links`). Add an entry whenever a new indexed page is added — never for `404.html` |
| `data/published.json` | CI-generated; never hand-edit |
| `.github/` | frozen-index, snapshot and live-smoke workflows + scripts (see CI above) |

## Verification before reporting done

1. `git diff a8a8354 -- index.html` — only the requested change, nothing else.
   `index-frozen.yml` fails the push if this is not empty.
2. `node .github/scripts/check-honest-copy.mjs` — exits 0, and the copy still says the projects
   are vibe coded rather than hand-built. `refresh-snapshot.yml` runs it on every push and pull
   request and `live-smoke.yml` on every deploy, so any of those runs fails if this is not clean.
   `node --test .github/scripts/guard-selftest.mjs` — exits 0, proving both the copy check and the
   404 test still fail when they should; run it after changing either guard or `404.html`.
3. Fetch the live page and confirm 200 plus the expected markup.
4. No horizontal overflow at 320 / 390 / 768 / 1280 px.
5. No requests to `api.github.com`; no console errors.
6. `sitemap.xml` parses, and every URL it lists returns 200.

## Deployment and secrets

- GitHub Pages builds automatically from `main:/`; wait for the build of the pushed commit
  before claiming something is live.
- Never commit, print or echo tokens, keys or `.env` values. Report secrets only by name.
- Commits go to `main`; push only when the user asked for the change to be live.
