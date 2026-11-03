# zakker111 — Portfolio

Static GitHub Pages portfolio.

## Files

- `index.html` — complete website (includes the cookie banner + human-only
  Google Analytics code, inline in `<head>`)
- `.nojekyll` — empty static-site marker
- `robots.txt` — crawler rules
- `AGENTS.md` — AI editing instructions
- `.github/workflows/pages.yml` — automatic GitHub Pages deployment

## GitHub setup

1. Create a GitHub repository named `portfolio` under `zakker111`.
2. Upload this package with the same folder structure.
3. Commit/push everything to the `main` branch.
4. Open **Settings → Pages**.
5. Under **Build and deployment → Source**, select **GitHub Actions**.
6. Open **Actions** and run **Deploy portfolio to GitHub Pages** if it did not start automatically.
7. After the workflow succeeds, the site is: https://zakker111.github.io/portfolio/

The workflow needs no Node, Python, npm install, build command, or personal access token. It uploads the repository root directly as the Pages artifact.

## Automatic deployment

Every push to `main` triggers the workflow. `workflow_dispatch` also allows a manual deployment from the Actions tab.

## Adding a project

The current page is a **static single file**: every project is a hand-written
`<article class="project">` block inside `#projects` in `index.html`. To add one:

1. Copy an existing `<article>` block (e.g. Pick One, project 07) and change:
   number `0N`, title, kind label, blurb, buttons (`href`s), preview SVG,
   `id="p-<slug>"` anchor, and the accent via `style="--accent:…"` if desired.
2. Add `.project:nth-child(N){animation-delay:…}` to the CSS block that lists
   the per-card entrance delays (keep it in sync with the card count).
3. External apps (no GitHub repo) skip the live "Updated …" check — give their
   footer span no `data-updated` attribute, like Pick One does.

There is **no `PROJECTS` array** anymore — ignore older instructions that
mention it. See `AGENTS.md` for the full structure reference.

## Local test

Open `index.html` directly, or run `python -m http.server 8000` in the repository root and open http://localhost:8000/.

## Troubleshooting

If Pages does not deploy, verify that the workflow exists at `.github/workflows/pages.yml`, Actions are enabled, the repository uses `main`, and Pages Source is **GitHub Actions**. Then inspect the latest workflow run under **Actions**.

The portfolio's GitHub API status indicators are optional enhancements; temporary API failures do not prevent the static page itself from loading.

## Weekly auto-refresh (GitHub Actions)

`.github/workflows/refresh.yml` runs on a schedule (Mondays + Thursdays, plus a
6-hourly snapshot keep-alive) and can be triggered any time from the **Actions**
tab ("Refresh portfolio" → Run workflow). Each run:

1. pulls your repo list from the GitHub API,
2. regenerates `data/published.json` (snapshot of non-fork, non-shelved repos),
3. checks every link it knows about — GitHub repos/READMEs via the API, Pages
   URLs via HEAD — and writes an audit trail to `data/link-report.txt`,
4. commits & pushes back to `main` only when something changed — which then
   triggers the Pages deploy automatically.

No secrets or extra setup needed; the built-in `GITHUB_TOKEN` is used.

⚠️ Note: the page was simplified to a fully static single file (hand-written
`<article>` cards, inline SVG previews, per-card live check in the browser).
The refresh script's older page-maintenance features (`LAST-UPDATED` stamp,
`AUTO-LINKS` block, `PROJECTS` array parsing) find no matching markup and are
skipped harmlessly — the script never breaks the page. Its main remaining job
is regenerating `data/published.json` and the link report.

## Analytics & cookie consent (Google Analytics)

The site now has a **cookie banner** and optional **Google Analytics 4**
tracking built into `index.html`. The rule of this site is simple:

> **It only tracks where human visitors come from — nothing more.**
> No ads, no user profiles, no personal data, no marketing cookies.
> Bots and crawlers are never tracked.

### How the cookie works

There is one first-party consent cookie called **`ga_consent`**. It stores
only the word `yes` or `no` for 365 days. Nothing else is ever written to it.

When a visitor opens the page, a small banner appears at the bottom with two
buttons and an explanation:

| Element | What it does |
|---|---|
| **Yes, track me** | Sets `ga_consent=yes`, then loads Google Analytics (gtag). Only after this click does GA set its own `_ga` cookie and send any hit to Google. |
| **No, don't track me** | Sets `ga_consent=no`. GA is **never loaded**, no analytics cookie is ever created, and no request goes to Google. The banner never returns for a year. |
| **Why?** (shown in the banner) | Explains that the site tracks *only where human visitors come from* (country/city and page viewed) — nothing more; bots are excluded automatically. |

On later visits the stored answer is respected silently: `yes` → GA loads
directly, `no` → GA never loads, absent → banner shows again.

### Human-only guarantee (bots are never counted)

Before even showing the banner, the script runs a `looksHuman()` check. A
visitor must pass **all** of these, otherwise nothing happens at all — no
banner, no cookie, no gtag script tag, no network request to Google:

1. Real browser environment (`document.createElement`, `navigator.plugins` exist).
2. `navigator.webdriver !== true` (blocks Selenium/Puppeteer automation).
3. User-Agent contains none of `bot, crawler, spider, headless, scraping, python, curl, wget, phantom, slurp`.
4. Tracking additionally requires an explicit human **Yes** click — a bot
   cannot press a button, so even a scripted scraper that fakes 1–3 still
   sends zero data.

So the only traffic that can ever reach your Google Analytics reports is a
real person in a real browser who clicked **Yes**. And what GA receives is
just: page viewed + coarse location derived from the connection (country/city)
+ generic device/browser info — with `ad_storage`, `ad_user_data` and
`ad_personalization` all hard-set to `denied`, IP addresses truncated at the
network level by GA4 itself (GA4 never logs or stores full IPs), and the `_ga`
cookie capped at ~11 months.

### How to connect it to Google Analytics (one-time setup)

1. Go to <https://analytics.google.com> → **Admin → Create property** → choose
   **GA4**, enter the site name/time zone/currency.
2. Under the property: **Data streams → Add stream → Web**, give the URL
   `https://zakker111.github.io/Portfolio/` and create the stream.
3. Copy the **Measurement ID** shown at the top of the stream details —
   it looks like `G-ABC1234DEF`.
4. Open `index.html` and find near the top of `<head>`:
   ```js
   window.GA_MEASUREMENT_ID = 'G-XXXXXXXXXX';
   ```
   Replace `'G-XXXXXXXXXX'` with your Measurement ID, save, commit, push.
   GitHub Actions deploys automatically.
5. That's it. Until you replace the placeholder, the code does **nothing**
   (safe default — no tracking at all).
6. Verify: open the live site as a normal browser, click **Yes, track me**,
   then in GA go to **Reports → Realtime** — a visit should appear within a
   couple of minutes. Clicking **No** produces no request at all (check
   DevTools → Network: no `google-analytics.com` call).

Optional extra safety in the GA console: **Admin → Data settings → Traffic
filtering → Define internal traffic / filter bot traffic** (GA also has a
built-in "exclude all known computer and internet traffic" option — turn it
on).

### Local test

Serve the folder (`python -m http.server 8000`), open http://localhost:8000/.
The banner appears; DevTools → Application → Cookies shows only `ga_consent`
after clicking Yes or No. With the placeholder ID, GA never loads even on Yes.

### Changing the wording

The banner text and buttons live in `showBanner()` inside the commented
"Google Analytics 4 — human-visitor-only tracking" block in `index.html`.
Keep both buttons: **Yes** must be what enables loading, **No** must leave
everything off, and the **Why** line should stay honest — human origin only,
nothing more.
