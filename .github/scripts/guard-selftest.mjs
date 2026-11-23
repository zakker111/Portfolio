// Proof that the guards can fail.
//
// A guard that always passes is worthless, so this runs each one against
// throwaway fixtures in the system temp directory and checks both outcomes:
// the honest-copy check must fail on a page that says "built by hand" and pass
// on a clean one, and the 404 test must pass on a page whose redirect map
// handles a near-miss URL and fail once that map is broken. The fixtures never
// live in the repository, so no bad copy is committed and nothing bad is ever
// deployed.
//
// Run it with the other guards:
//   node --test .github/scripts/guard-selftest.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const scripts = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(scripts, '..', '..');

// Run a guard as its own process, the way CI runs it, so the test asserts on
// the exit code CI actually reacts to.
function runGuard(args, { cwd = repoRoot, env = {} } = {}) {
  const childEnv = { ...process.env, ...env };
  // This file runs under `node --test`, which marks child processes with
  // NODE_TEST_CONTEXT; inherited, it makes the spawned guard report results in
  // the test runner's binary format instead of readable output.
  delete childEnv.NODE_TEST_CONTEXT;

  const result = spawnSync(process.execPath, args, {
    cwd,
    encoding: 'utf8',
    env: childEnv,
  });
  assert.equal(result.error, undefined, `could not run node ${args.join(' ')}`);
  return result;
}

// A throwaway directory to hold fixture pages; removed by the caller.
function fixtureDir() {
  return mkdtempSync(join(tmpdir(), 'guard-selftest-'));
}

// Pass/fail counts from a node:test run, whichever reporter ran: the spec
// reporter on a TTY (or Node 22+) prints "ℹ pass 6", a TAP run prints
// "# pass 6".
function testCounts(stdout) {
  const count = label => Number((stdout.match(new RegExp(`(?:ℹ|#) ${label} (\\d+)`)) || [])[1]);
  return { pass: count('pass'), fail: count('fail') };
}

const copyCheck = join(scripts, 'check-honest-copy.mjs');
const redirectTest = join(scripts, 'test-404.mjs');

test('honest-copy check fails on a fixture page that says "built by hand"', () => {
  const dir = fixtureDir();
  try {
    writeFileSync(
      join(dir, 'index.html'),
      '<h1>Portfolio</h1><p>Every card on this page was built by hand.</p>'
    );

    const result = runGuard([copyCheck], { cwd: dir });

    assert.equal(
      result.status,
      1,
      `expected the copy check to fail on hand-built copy, got exit ${result.status}:\n${result.stdout}${result.stderr}`
    );
    assert.match(result.stderr, /::error file=index\.html::/, result.stderr);
    assert.match(result.stderr, /by hand/, result.stderr);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('honest-copy check passes on a clean fixture page', () => {
  const dir = fixtureDir();
  try {
    writeFileSync(
      join(dir, 'index.html'),
      '<h1>Portfolio</h1><p>These projects were vibe coded with AI.</p>'
    );

    const result = runGuard([copyCheck], { cwd: dir });

    assert.equal(
      result.status,
      0,
      `expected the copy check to pass on clean copy, got exit ${result.status}:\n${result.stdout}${result.stderr}`
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('404 test passes on a fixture page whose redirect map handles a near-miss URL', () => {
  const dir = fixtureDir();
  try {
    const page = join(dir, '404.html');
    copyFileSync(join(repoRoot, '404.html'), page);

    // The test file is run directly rather than under --test: a nested node
    // test runner refuses to run files and would exit 0 without testing
    // anything.
    const result = runGuard([redirectTest], {
      env: { PORTFOLIO_404_PAGE: page },
    });

    assert.equal(
      result.status,
      0,
      `expected the 404 test to pass on a working redirect map, got exit ${result.status}:\n${result.stdout}${result.stderr}`
    );
    const counts = testCounts(result.stdout);
    assert.ok(counts.pass >= 1, `the 404 test ran no tests:\n${result.stdout}`);
    assert.equal(counts.fail, 0, `the 404 test reported failures on a working map:\n${result.stdout}`);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('404 test fails on a fixture page whose redirect map is broken', () => {
  const dir = fixtureDir();
  try {
    const html = readFileSync(join(repoRoot, '404.html'), 'utf8');
    const broken = html.replace("var BASE = '/Portfolio/';", "var BASE = '/';");
    assert.notEqual(
      broken,
      html,
      '404.html no longer declares BASE as "/Portfolio/", so this fixture cannot break it — update the replacement'
    );

    const page = join(dir, '404.html');
    writeFileSync(page, broken);

    const result = runGuard([redirectTest], {
      env: { PORTFOLIO_404_PAGE: page },
    });

    assert.equal(
      result.status,
      1,
      `expected the 404 test to fail on a broken redirect map, got exit ${result.status}:\n${result.stdout}${result.stderr}`
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
