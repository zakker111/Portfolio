// Builds data/published.json for the portfolio: the latest commit date of every
// repository a project card points at. Runs in CI with GITHUB_TOKEN (5 000
// requests/hour), so the page never has to touch api.github.com itself.
//
// Repos are discovered from the cards in index.html (data-repo="owner/name"),
// so adding a card is enough — no list to keep in sync here.
//
// generated_at is the time the project data last changed, not the last time
// this script ran. When nothing changed, the file is left untouched, so the
// page's "snapshot <time>" stays honest instead of claiming a refresh that
// changed no data.
import fs from 'node:fs';

const TOKEN = process.env.GH_TOKEN || process.env.GITHUB_TOKEN || '';
const API = 'https://api.github.com';

const html = fs.readFileSync('index.html', 'utf8');
const repos = [...html.matchAll(/data-repo="([^"\s]+)"/g)]
  .map(m => m[1].trim())
  .filter((v, i, a) => a.indexOf(v) === i);

if (!repos.length) {
  console.error('No data-repo attributes found in index.html');
  process.exit(1);
}

const headers = {
  Accept: 'application/vnd.github+json',
  'User-Agent': 'portfolio-snapshot',
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

const rows = [];
for (const full of repos) {
  const [owner, name] = full.split('/');
  try {
    const res = await fetch(`${API}/repos/${owner}/${name}/commits?per_page=1`, { headers });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const commits = await res.json();
    if (!Array.isArray(commits) || !commits[0]) throw new Error('no commits');
    const c = commits[0];
    rows.push({
      name,
      full_name: full,
      pushed_at: c.commit?.committer?.date || c.commit?.author?.date || null,
      sha: c.sha || '',
    });
    console.log(`${full}: ${rows.at(-1).pushed_at}`);
  } catch (error) {
    console.warn(`${full}: ${error.message} (skipped)`);
  }
}

if (!rows.length) {
  console.error('Every lookup failed — leaving the existing snapshot untouched');
  process.exit(1);
}

const OUT = 'data/published.json';

// Compare only the fields the page uses. Key order and formatting do not
// matter, and a new generated_at alone must not cause a commit.
function fingerprint(repos) {
  return (Array.isArray(repos) ? repos : [])
    .map(row => [row.name, row.full_name, row.pushed_at, row.sha].join('\u0000'))
    .sort()
    .join('\n');
}

let previous = null;
try {
  previous = JSON.parse(fs.readFileSync(OUT, 'utf8'));
} catch {
  // No readable snapshot yet: write a fresh one below.
}

const sorted = rows.sort((a, b) => a.name.localeCompare(b.name));
const unchanged =
  previous &&
  typeof previous.generated_at === 'string' &&
  fingerprint(previous.repos) === fingerprint(sorted);

if (unchanged) {
  console.log('Project data unchanged — keeping the snapshot and its generated_at');
  process.exit(0);
}

const out = {
  generated_at: new Date().toISOString(),
  repos: sorted,
};

fs.mkdirSync('data', { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n');
console.log(`Wrote ${OUT} with ${rows.length} repos`);
