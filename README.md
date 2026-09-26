# zakker111 — Portfolio

Static GitHub Pages portfolio.

## Files

- `index.html` — complete website
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

Open `index.html`, find the `PROJECTS` array near the top of the `<script>` at the bottom, and add one entry (title, blurb, repo, link, color). Cards, numbering and counters update automatically. See `AGENTS.md` for the field reference.

## Local test

Open `index.html` directly, or run `python -m http.server 8000` in the repository root and open http://localhost:8000/.

## Troubleshooting

If Pages does not deploy, verify that the workflow exists at `.github/workflows/pages.yml`, Actions are enabled, the repository uses `main`, and Pages Source is **GitHub Actions**. Then inspect the latest workflow run under **Actions**.

The portfolio's GitHub API status indicators are optional enhancements; temporary API failures do not prevent the static page itself from loading.
