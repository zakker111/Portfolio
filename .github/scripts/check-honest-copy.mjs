#!/usr/bin/env node
// Honest-copy guard: fails when a page claims the site or its projects were
// hand-built.
//
// about.html says most projects are vibe coded, and that claim has to stay
// true. This guard fails the CI run when hand-built copy ("by hand",
// "hand-crafted", "built from scratch", "built by me", ...) reappears on any
// page, instead of relying on someone remembering to grep before a push. It
// only reads the pages; it never rewrites them.
//
// Run it before pushing copy changes:
//   node .github/scripts/check-honest-copy.mjs

import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();

// One entry per banned phrasing, matched case-insensitively against the page's
// text: tags are stripped and entities decoded first, so "by <em>hand</em>" and
// "by&nbsp;hand" are caught as well. Adding a phrasing here is the way to close
// a gap; a page must not be worded around the list.
const CLAIMS = [
  [/\bby[\s\u2011-]?hand\b/i, 'by hand'],
  [/\bhand[\s\u2011-]?(built|coded|crafted|made|written)\b/i, 'hand-built'],
  [/\bhandmade\b/i, 'handmade'],
  [/\b(built|coded|made|written|designed)\b[^.<]{0,30}?\bfrom scratch\b/i, 'from scratch'],
  [/\bmanually (built|coded|made|written)\b/i, 'manually built'],
  [/\bself[\s\u2011-]?(built|coded|made|written)\b/i, 'self-built'],
  [/\bmy own (two )?hands\b/i, 'my own hands'],
  [/\b(built|coded|written|designed) by (me|myself)\b/i, 'built by me'],
  [/\bi (built|coded|wrote|created|designed) (this|the site|the whole site|every)\b/i, 'I built this'],
  [/\bevery line of (code|it|this)\b/i, 'every line of code'],
];

// The readable text of a page, so markup cannot hide a claim mid-phrase.
function pageText(html) {
  return html
    .replace(/<!--[\s\S]*?-->/g, ' ') // comments are not copy
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;|&#0*160;|&#x0*a0;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&#0*39;|&#x0*27;|&apos;|&rsquo;/gi, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

const pages = readdirSync(root).filter((name) => name.endsWith('.html')).sort();

// A page list of zero would make the check pass without checking anything.
if (pages.length === 0) {
  console.error('::error::No .html pages found to check, so hand-built copy could not be verified.');
  process.exit(1);
}

let claims = 0;

for (const page of pages) {
  const text = pageText(readFileSync(join(root, page), 'utf8'));
  const hits = [];

  for (const [pattern, label] of CLAIMS) {
    const match = pattern.exec(text);
    if (match) hits.push({ label, found: match[0], at: match.index });
  }

  if (hits.length === 0) {
    console.log(`${page}: no hand-built claims.`);
    continue;
  }

  for (const hit of hits) {
    const start = Math.max(0, hit.at - 40);
    const snippet = text.slice(start, hit.at + hit.found.length + 40).trim();
    console.error(
      `::error file=${page}::Hand-built claim "${hit.found}" (${hit.label}). ` +
        'The site is described as vibe coded, so reword it instead of loosening this check.'
    );
    console.error(`  ${page}: …${snippet}…`);
    claims += 1;
  }
}

if (claims > 0) {
  console.error(`\n${claims} hand-built claim(s) found.`);
  process.exit(1);
}

console.log('No hand-built claims on any page.');
