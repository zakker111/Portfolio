#!/usr/bin/env node
// Report failed guard runs, and close the report when the guards recover.
//
// The guards that keep this repository honest — the honest-copy check, the 404
// redirect-map test and the frozen-index check — can go red on a push or a pull
// request between two Pages deployments, when nothing else is watching. This
// runs from guard-alert.yml when one of those workflows finishes, and:
//
// - on a failure, opens the single guard-failure issue or comments on it, so
//   every failure lands in one place instead of a new issue per run;
// - on a green run of the default branch, closes that issue once no watched
//   workflow is still red, naming the passing run — a closed issue means the
//   next failure opens a fresh one, so nothing is swallowed.
//
// It only reads workflow runs and writes that one issue; it never touches the
// pages, data or workflows.

import { pathToFileURL } from 'node:url';

// The one issue every guard failure is reported in. Keep it stable: it is how
// the open issue is found again, so a second issue is never opened, and how a
// recovery finds what to close.
const TITLE = 'CI guard failed';

// Workflow name → workflow file, for the workflows that carry a guard. The
// name is what GitHub reports on a run, the file is what the runs API accepts.
export const WATCHED = {
  'Refresh update snapshot': 'refresh-snapshot.yml',
  'Frozen index.html': 'index-frozen.yml',
  'Live portfolio smoke test': 'live-smoke.yml',
};

const INTRO = `A guard that keeps the portfolio honest failed. This issue is reused for every later failure — one comment per new failure, no second issue — so a red run between two deploys is not missed. It closes itself when the guards pass again on the default branch.

The guards reported here:

- **honest-copy check** — the projects are vibe coded, and no page may claim otherwise
- **404 redirect-map test** — near-miss URLs must recover, unknown URLs must stay on the 404 page
- **frozen \`index.html\` check** — the homepage is frozen at \`a8a8354\`
- **guard self-test** — the checks above must still fail when they should`;

// Step name → the guard it protects, for the workflows that run the guards as
// steps. A job that fails on a step not listed here (checkout, setup) is
// reported as the job failing, because the guards never ran.
const GUARD_STEP = {
  'Check pages for hand-built claims': 'honest-copy check',
  'Test 404 redirect map': '404 redirect-map test',
  'Prove the guards can fail': 'guard self-test',
};

function failedSteps(job) {
  return (job.steps || []).filter(step => step.conclusion === 'failure').map(step => step.name);
}

// The guard failures inside one finished run, or [] when the run went red
// somewhere that is not a guard. The live-smoke `smoke` job checks the deployed
// site and the refresh-snapshot `snapshot` job only refreshes data, so neither
// is reported here.
export function guardFailures(workflow, jobs) {
  const failures = [];

  for (const job of jobs) {
    if (job.conclusion !== 'failure') continue;
    const steps = failedSteps(job);
    const named = steps.map(step => GUARD_STEP[step]).filter(Boolean).join(' + ');

    if (workflow === 'Frozen index.html') {
      failures.push({ guard: 'frozen `index.html` check', job: job.name, steps });
    } else if (workflow === 'Refresh update snapshot' && job.name === 'test') {
      failures.push({ guard: named || 'guard checks (the job failed before they could run)', job: job.name, steps });
    } else if (workflow === 'Live portfolio smoke test' && job.name === 'honest copy') {
      failures.push({ guard: named || 'honest-copy check', job: job.name, steps });
    }
  }

  return failures;
}

// Identifies this exact failure, so re-running the alert for the same red run
// does not comment twice.
export function markerFor(run, failures) {
  return `<!-- guard-alert:${run.head_sha}:${failures.map(failure => failure.guard).join('|')} -->`;
}

// The failure itself, as the issue body or comment shows it.
export function failureDetails(run, failures) {
  const lines = [
    `- **Workflow:** ${run.name}`,
    `- **Run:** [${run.id}](${run.html_url}) — commit \`${run.head_sha.slice(0, 7)}\` on \`${run.head_branch}\``,
  ];

  for (const failure of failures) {
    const steps = failure.steps.length
      ? ` — failing step${failure.steps.length > 1 ? 's' : ''} ${failure.steps.map(step => `"${step}"`).join(', ')}`
      : '';
    lines.push(`- **Failed:** ${failure.guard} (job \`${failure.job}\`)${steps}`);
  }

  return lines.join('\n');
}

// The comment posted when the guards recover; it names the run that proved it.
// Its marker is deliberately different from the failure marker so a later
// failure is never mistaken for something already reported.
export function recoveredNote(run) {
  return `Guards are green again, so this issue is closed.\n\n` +
    `- **Passing run:** [${run.name}](${run.html_url}) — commit \`${run.head_sha.slice(0, 7)}\` on \`${run.head_branch}\`\n\n` +
    `<!-- guard-alert-recovered:${run.head_sha} -->`;
}

async function api(token, path, init = {}) {
  const response = await fetch(`https://api.github.com${path}`, {
    ...init,
    headers: {
      accept: 'application/vnd.github+json',
      authorization: `Bearer ${token}`,
      'content-type': 'application/json',
      'user-agent': 'guard-alert',
      'x-github-api-version': '2022-11-28',
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`${init.method || 'GET'} ${path} failed: ${response.status} ${await response.text()}`);
  }

  return response.status === 204 ? null : response.json();
}

// Latest completed run of every watched workflow on `branch` that still shows a
// guard failure. A green run of one guard workflow must not close the issue
// while another guard is still red.
async function stillFailing(token, repo, branch) {
  const failing = [];

  for (const [name, workflow] of Object.entries(WATCHED)) {
    const { workflow_runs: runs } = await api(
      token,
      `/repos/${repo}/actions/workflows/${workflow}/runs?branch=${encodeURIComponent(branch)}&status=completed&per_page=1`
    );
    const latest = runs[0];
    if (!latest || latest.conclusion !== 'failure') continue;

    const { jobs } = await api(token, `/repos/${repo}/actions/runs/${latest.id}/jobs?filter=latest&per_page=100`);
    const failures = guardFailures(name, jobs);
    if (failures.length > 0) failing.push({ name, failures });
  }

  return failing;
}

// Close the issue from a green run, but only for the default branch (that is
// where "the guards are green" is meaningful) and only when nothing else is
// still red.
async function closeIfRecovered(token, repo, run, issue) {
  const { default_branch: branch } = await api(token, `/repos/${repo}`);

  if (run.head_branch !== branch) {
    console.log(`${run.name} passed on a branch other than ${branch}, so ${issue.html_url} stays open until a run on ${branch} passes.`);
    return;
  }

  const failing = await stillFailing(token, repo, branch);
  if (failing.length > 0) {
    const detail = failing.map(item => `${item.name} (${item.failures.map(failure => failure.guard).join(', ')})`).join('; ');
    console.log(`Leaving ${issue.html_url} open: still failing on ${branch} in ${detail}.`);
    return;
  }

  await api(token, `/repos/${repo}/issues/${issue.number}/comments`, {
    method: 'POST',
    body: JSON.stringify({ body: recoveredNote(run) }),
  });
  await api(token, `/repos/${repo}/issues/${issue.number}`, {
    method: 'PATCH',
    body: JSON.stringify({ state: 'closed', state_reason: 'completed' }),
  });
  console.log(`::notice::Closed ${issue.html_url}: ${run.name} passed on ${branch}.`);
}

async function main() {
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
  const repo = process.env.REPO || process.env.GITHUB_REPOSITORY;
  const runId = process.env.RUN_ID;
  if (!token || !repo || !runId) {
    throw new Error('GH_TOKEN, REPO and RUN_ID must be set');
  }

  const run = await api(token, `/repos/${repo}/actions/runs/${runId}`);
  if (run.conclusion !== 'failure' && run.conclusion !== 'success') {
    console.log(`Run ${run.id} (${run.name}) concluded ${run.conclusion}, so there is nothing to report.`);
    return;
  }

  const openIssues = await api(token, `/repos/${repo}/issues?state=open&per_page=100`);
  const issue = openIssues.find(open => !open.pull_request && open.title === TITLE);

  if (run.conclusion === 'success') {
    if (!issue) {
      console.log(`No open "${TITLE}" issue, so the passing ${run.name} run needed nothing.`);
      return;
    }
    await closeIfRecovered(token, repo, run, issue);
    return;
  }

  const { jobs } = await api(token, `/repos/${repo}/actions/runs/${run.id}/jobs?filter=latest&per_page=100`);
  const failures = guardFailures(run.name, jobs);
  if (failures.length === 0) {
    console.log(`Run ${run.id} (${run.name}) failed, but not in a guard job, so no issue was opened.`);
    return;
  }

  const details = failureDetails(run, failures);
  const marker = markerFor(run, failures);

  if (!issue) {
    const created = await api(token, `/repos/${repo}/issues`, {
      method: 'POST',
      body: JSON.stringify({ title: TITLE, body: `${INTRO}\n\n## Latest failure\n\n${details}\n\n${marker}\n` }),
    });
    console.log(`::notice::Opened ${created.html_url} for the failed ${run.name} run.`);
    return;
  }

  const comments = await api(token, `/repos/${repo}/issues/${issue.number}/comments?per_page=100`);
  // The first failure is recorded in the issue body, later ones in comments, so
  // a re-run of this job for a failure that is already there adds nothing.
  const reported = [issue.body || '', ...comments.map(comment => comment.body || '')];
  if (reported.some(text => text.includes(marker))) {
    console.log(`This failure is already reported in ${issue.html_url}.`);
    return;
  }

  await api(token, `/repos/${repo}/issues/${issue.number}/comments`, {
    method: 'POST',
    body: JSON.stringify({ body: `Another guard failure.\n\n${details}\n\n${marker}` }),
  });
  console.log(`::notice::Added the failed ${run.name} run to ${issue.html_url}.`);
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  main().catch(error => {
    console.error(`::error::${error.message}`);
    process.exit(1);
  });
}
