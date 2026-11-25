// Live smoke test: opens the deployed portfolio in a phone-sized Chromium and
// checks that every page loads and that 404.html still recovers near-miss URLs.
// Run by .github/workflows/live-smoke.yml after each successful Pages
// deployment, on a six-hour schedule, or by hand; BASE_URL points it at a
// local server instead.
//
// Locally: npm install --no-save --no-package-lock playwright@1.65.1
//          npx playwright install chromium
//          node .github/scripts/live-smoke.mjs
import { chromium } from 'playwright';

const BASE = (process.env.BASE_URL || 'https://zakker111.github.io/portfolio/').replace(
  /\/?$/,
  '/'
);
const BASE_PATH = new URL(BASE).pathname;
const urlFor = path => new URL(path, BASE).href;
const pathOf = url => new URL(url).pathname;

// The four pages and a word their <title> must contain.
const PAGES = [
  { path: '', title: 'Projects' },
  { path: 'tools.html', title: 'Tools' },
  { path: 'about.html', title: 'About' },
  { path: 'links.html', title: 'Links' }
];

// Near-miss URLs that GitHub Pages answers with 404.html; its script must send
// them on to the real page. %20 is what a URL pasted with a trailing space becomes.
const REDIRECTS = [
  { path: 'tools/', expected: 'tools.html' },
  { path: '%20', expected: 'index.html' }
];

const UNKNOWN = 'no-such-page';

let failures = 0;
function check(ok, message) {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${message}`);
  if (!ok) failures++;
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });

  for (const { path, title } of PAGES) {
    const name = path || '(home)';
    const response = await page.goto(urlFor(path), { waitUntil: 'domcontentloaded' });
    const status = response ? response.status() : 'no response';
    check(response?.status() === 200, `${name} loads with HTTP ${status}`);
    const actualTitle = await page.title();
    check(actualTitle.includes(title), `${name} renders its page ("${actualTitle}")`);
  }

  for (const { path, expected } of REDIRECTS) {
    const target = BASE_PATH + expected;
    // 404.html redirects from <head>, which can abort the goto() navigation;
    // only the URL the visitor ends on is under test.
    await page.goto(urlFor(path), { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForURL(url => url.pathname === target).catch(() => {});
    const finalPath = pathOf(page.url());
    check(finalPath === target, `${path} redirects to ${target} (got ${finalPath})`);
  }

  const unknown = urlFor(UNKNOWN);
  const response = await page.goto(unknown, { waitUntil: 'domcontentloaded' });
  const status = response ? response.status() : 'no response';
  check(response?.status() === 404, `unknown URL answers HTTP ${status}`);
  // 404.html would redirect from <head>; give that navigation time to happen
  // (or not) before deciding the URL stayed where it was.
  await page.waitForTimeout(500);
  check(
    pathOf(page.url()) === BASE_PATH + UNKNOWN,
    `unknown URL is not redirected (still ${pathOf(page.url())})`
  );
} finally {
  await browser.close();
}

if (failures) {
  console.error(`${failures} live check(s) failed`);
  process.exit(1);
}
console.log('All live smoke checks passed');
