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
    // An empty target means the site root (/portfolio/), which serves index.html.
    const file = page || 'index.html';
    assert.ok(
      SITE_PAGES.includes(file),
      `alias "${alias}" points at "${page}", which is not one of ${SITE_PAGES.join(', ')}`
    );
    assert.ok(existsSync(join(repoRoot, file)), `alias "${alias}" points at missing file "${file}"`);
  }
});

test('the redirect map is rooted at the project site path', () => {
  assert.match(redirectCode, /var\s+BASE\s*=\s*['"]\/portfolio\/['"];/);
});

test('near-miss URLs recover to the intended page', () => {
  const cases = [
    ['/portfolio/tools/', '/portfolio/tools.html'],
    ['/portfolio/tools', '/portfolio/tools.html'],
    ['/portfolio/TOOLS', '/portfolio/tools.html'],
    ['/portfolio/Tools/', '/portfolio/tools.html'],
    ['/portfolio/tool', '/portfolio/tools.html'],
    ['/portfolio/about', '/portfolio/about.html'],
    ['/portfolio/about/', '/portfolio/about.html'],
    ['/portfolio/other-stuff', '/portfolio/about.html'],
    ['/portfolio/links/', '/portfolio/links.html'],
    ['/portfolio/link', '/portfolio/links.html'],
    ['/portfolio/all-links', '/portfolio/links.html'],
    ['/portfolio/projects', '/portfolio/'],
    ['/portfolio/project', '/portfolio/'],
    ['/portfolio/home/', '/portfolio/'],
    ['/portfolio/start', '/portfolio/'],
    ['/portfolio/index', '/portfolio/index.html'],
    ['/portfolio/index.html/', '/portfolio/index.html'],
    ['/portfolio/tools%2F', '/portfolio/tools.html']
  ];
  for (const [pathname, expected] of cases) {
    assert.equal(redirect(pathname), expected, pathname);
  }
});

test('trailing spaces and zero-width characters are ignored', () => {
  const cases = [
    ['/portfolio/%20', '/portfolio/index.html'],
    ['/portfolio/%20/', '/portfolio/index.html'],
    ['/portfolio/%C2%A0', '/portfolio/index.html'],
    ['/portfolio/%E2%80%8B', '/portfolio/index.html'],
    ['/portfolio/%0A', '/portfolio/index.html'],
    ['/portfolio/tools/%20', '/portfolio/tools.html'],
    ['/portfolio/%20tools', '/portfolio/tools.html']
  ];
  for (const [pathname, expected] of cases) {
    assert.equal(redirect(pathname), expected, pathname);
  }
});

test('query string and hash survive the redirect', () => {
  assert.equal(redirect('/portfolio/tools', '?utm=x', '#tools'), '/portfolio/tools.html?utm=x#tools');
  assert.equal(redirect('/portfolio/%20', '?fbclid=1', '#top'), '/portfolio/index.html?fbclid=1#top');
});

test('unknown, malformed and out-of-scope URLs stay on the 404 page', () => {
  const cases = [
    '/portfolio/no-such-page',
    '/portfolio/index.htm',
    '/portfolio/portfolio/tools',
    '/portfolio/index.html',
    '/portfolio/links.html',
    '/other/tools/',
    '/portfolio/%E0%A4%A'
  ];
  for (const pathname of cases) {
    assert.equal(redirect(pathname), null, pathname);
  }
});
