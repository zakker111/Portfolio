# AGENTS.md — rules for this repository

Portfolio site of **zakker111**, served by GitHub Pages (legacy build, source `main:/`).

Live: https://zakker111.github.io/Portfolio/

## The strict rule: `index.html` is the projects page and must stay as it is

`index.html` is **standalone and frozen**. It is the whole site as designed; it must keep
looking and behaving exactly as it does today.

The canonical, approved version is commit **`3a3d6b3`**. At any time:

```bash
git diff 3a3d6b3 -- index.html    # must be empty, or only the one link explicitly requested
```

must show nothing except changes the user asked for **in that same request** — currently exactly two
approved items: the footer link `Other stuff ↗` and the approved card look, which is now folded
into the original `.card-grid`, `.project`, `.preview` and `.project-info` rules (see
"Approved card look" below).

### Never do this to `index.html`

- Do not restructure it: no reordering of the hero, `#projects` or `#tools`, no new sections.
- Do not restyle it: do not touch the inline `<style>` block, the CSS variables, the
  `.card-grid` breakpoints (1 col ≤760px, 2 cols 761–1079px, 3 cols ≥1080px), the type scale,
  the colours or the spacing — with the single exception of the approved card look described
  below, which must stay exactly as it is.
- Do not edit, replace or remove the 9 project cards: their order, `--accent` colours, preview
  SVGs, numbers, descriptions, tags and the 21 project/source links stay byte-identical.
- Do not change the header nav (`Projects` · `Tools`) or add nav items on your own.
- Do not change the hero copy, the section headers, the footer text or the cookie banner.
- Do not re-add a link or page that was removed unless the user asks for it again.
- Do not reformat, "tidy" or prettify the file. It is one long line-per-block by design.

### The only allowed edits to `index.html`

Explicitly requested, additive, one at a time:

- one new card in the existing `#tools` grid, using the existing card markup, or
- one new link pointing at an extra page (e.g. the footer link `Other stuff ↗` → `about.html`),
  written with the existing footer/affordance markup and no new CSS.

If a request seems to need more than that on `index.html`, stop and ask.

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

## Extra content lives on separate pages

New material (about me, languages, tools, notes, anything else) goes into its **own page**
next to `index.html`, never into `index.html`:

- reuse `assets/site.css` (the stylesheet extracted from `index.html`) so the style is identical;
- use the existing components: `section.hero` + `.kicker` + `h1` + `p.intro` + `.hero-link`,
  `.section-head`, `.card-grid` > `article.project.tool` with `.preview`, `.monogram`,
  `.project-info`, `.number`, `.tags`, `.tag`, `.actions`, `.btn primary`;
- give each page `<title>`, `meta description`, `link rel="canonical"` and the shared favicon;
- link it from `index.html` with **one** small link, only when asked.

## Data: update labels come from the CI snapshot

The "Updated …" labels under each project read `data/published.json`, a snapshot committed
every six hours by `.github/workflows/refresh-snapshot.yml` (generator:
`.github/scripts/build-snapshot.mjs`).

- The page must never call `api.github.com` from the browser.
- Do not remove the `.github/` workflow or script, and do not add a client-side GitHub fetch.

## Files

| Path | Rule |
| --- | --- |
| `index.html` | the projects page — frozen, see above |
| `about.html` | extra page ("Other stuff"): languages + tools cards |
| `assets/site.css` | shared stylesheet copied from `index.html`; keep in sync when the homepage style legitimately changes |
| `og-image.png` | 1200×630 social card |
| `robots.txt`, `sitemap.xml` | crawling; the sitemap lists the homepage (extra pages get an entry only when they should be indexed) |
| `data/published.json` | CI-generated; never hand-edit |
| `.github/` | snapshot workflow + script |

## Verification before reporting done

1. `git diff 3a3d6b3 -- index.html` — only the requested change, nothing else.
2. Fetch the live page and confirm 200 plus the expected markup.
3. No horizontal overflow at 320 / 390 / 768 / 1280 px.
4. No requests to `api.github.com`; no console errors.
5. `sitemap.xml` parses, and every URL it lists returns 200.

## Deployment and secrets

- GitHub Pages builds automatically from `main:/`; wait for the build of the pushed commit
  before claiming something is live.
- Never commit, print or echo tokens, keys or `.env` values. Report secrets only by name.
- Commits go to `main`; push only when the user asked for the change to be live.
