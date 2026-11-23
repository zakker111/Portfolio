// Tests the redirect map in 404.html by running its real <script> against fake
// locations. The map is read from the file, never duplicated here, so a change
// that stops recovering a near-miss URL fails this test. Set PORTFOLIO_404_PAGE
// to point it at a fixture page instead (guard-selftest.mjs uses that to prove
// this test can fail).
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const pageFile = process.env.PORTFOLIO_404_PAGE || join(repoRoot, '404.html');
const html = readFileSync(pageFile, 'utf8');

const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map(m => m[1]);
const redirectCode = scripts.find(code => /var\s+BASE\s*=/.test(code) && /var\s+PAGES\s*=/.test(code));
assert.ok(redirectCode, '404.html must keep the redirect script with BASE and PAGES');

const runRedirect = new Function('location', redirectCode);

const mapMatch = redirectCode.match(/var\s+PAGES\s*=\s*\{([\s\S]*?)\};/);
assert.ok(mapMatch, '404.html redirect script must define a PAGES object');
const PAGES = new Function('return {' + mapMatch[1] + '}')();

// Pages that exist on the site and may be a redirect target.
const SITE_PAGES = ['index.html', 'tools.html', 'about.html', 'links.html'];

// Run the 404 page's script for one URL and return where it would send the
// visitor, or null when it leaves the 404 page alone.
function redirect(pathname, search = '', hash = '') {
  const calls = [];
  runRedirect({ pathname, search, hash, replace: url => calls.push(url) });
  return calls.length ? calls[calls.length - 1] : null;
}

test('every alias in the map points at a real page', () => {
  for (const [alias, page] of Object.entries(PAGES)) {
    // An empty target means the site root (/Portfolio/), which serves index.html.
    const file = page || 'index.html';
    assert.ok(
      SITE_PAGES.includes(file),
      `alias "${alias}" points at "${page}", which is not one of ${SITE_PAGES.join(', ')}`
    );
    assert.ok(existsSync(join(repoRoot, file)), `alias "${alias}" points at missing file "${file}"`);
  }
});

test('the redirect map is rooted at the project site path', () => {
  assert.match(redirectCode, /var\s+BASE\s*=\s*['"]\/Portfolio\/['"];/);
});

test('near-miss URLs recover to the intended page', () => {
  const cases = [
    ['/Portfolio/tools/', '/Portfolio/tools.html'],
    ['/Portfolio/tools', '/Portfolio/tools.html'],
    ['/Portfolio/TOOLS', '/Portfolio/tools.html'],
    ['/Portfolio/Tools/', '/Portfolio/tools.html'],
    ['/Portfolio/tool', '/Portfolio/tools.html'],
    ['/Portfolio/about', '/Portfolio/about.html'],
    ['/Portfolio/about/', '/Portfolio/about.html'],
    ['/Portfolio/other-stuff', '/Portfolio/about.html'],
    ['/Portfolio/links/', '/Portfolio/links.html'],
    ['/Portfolio/link', '/Portfolio/links.html'],
    ['/Portfolio/all-links', '/Portfolio/links.html'],
    ['/Portfolio/projects', '/Portfolio/'],
    ['/Portfolio/project', '/Portfolio/'],
    ['/Portfolio/home/', '/Portfolio/'],
    ['/Portfolio/start', '/Portfolio/'],
    ['/Portfolio/index', '/Portfolio/index.html'],
    ['/Portfolio/index.html/', '/Portfolio/index.html'],
    ['/Portfolio/tools%2F', '/Portfolio/tools.html']
  ];
  for (const [pathname, expected] of cases) {
    assert.equal(redirect(pathname), expected, pathname);
  }
});

test('trailing spaces and zero-width characters are ignored', () => {
  const cases = [
    ['/Portfolio/%20', '/Portfolio/index.html'],
    ['/Portfolio/%20/', '/Portfolio/index.html'],
    ['/Portfolio/%C2%A0', '/Portfolio/index.html'],
    ['/Portfolio/%E2%80%8B', '/Portfolio/index.html'],
    ['/Portfolio/%0A', '/Portfolio/index.html'],
    ['/Portfolio/tools/%20', '/Portfolio/tools.html'],
    ['/Portfolio/%20tools', '/Portfolio/tools.html']
  ];
  for (const [pathname, expected] of cases) {
    assert.equal(redirect(pathname), expected, pathname);
  }
});

test('query string and hash survive the redirect', () => {
  assert.equal(redirect('/Portfolio/tools', '?utm=x', '#tools'), '/Portfolio/tools.html?utm=x#tools');
  assert.equal(redirect('/Portfolio/%20', '?fbclid=1', '#top'), '/Portfolio/index.html?fbclid=1#top');
});

test('unknown, malformed and out-of-scope URLs stay on the 404 page', () => {
  const cases = [
    '/Portfolio/no-such-page',
    '/Portfolio/index.htm',
    '/Portfolio/Portfolio/tools',
    '/Portfolio/index.html',
    '/Portfolio/links.html',
    '/other/tools/',
    '/Portfolio/%E0%A4%A'
  ];
  for (const pathname of cases) {
    assert.equal(redirect(pathname), null, pathname);
  }
});
