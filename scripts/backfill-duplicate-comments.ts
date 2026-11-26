#!/usr/bin/env bun

declare global {
  var process: {
    env: Record<string, string | undefined>;
    exit(code?: number): never;
  };
}

interface GitHubIssue {
  number: number;
  title: string;
  user: { id: number };
  created_at: string;
  pull_request?: unknown;
}

interface GitHubComment {
  id: number;
  body: string;
  created_at: string;
  user: { type: string; id: number } | null;
}

const REQUEST_TIMEOUT_MS = 30000;
const MAX_PAGES = 200;
const PER_PAGE = 100;
const MAX_RETRY_DELAY_MS = 60000;
const TRIGGER_DELAY_MS = 1000;
const DEFAULT_OWNER = "anthropics";
const DEFAULT_REPO = "claude-code";
const DEFAULT_MAX_ISSUE = 4050;
const DEFAULT_MIN_ISSUE = 1;

function isSafeSlug(value: string): boolean {
  return /^[A-Za-z0-9_.-]{1,100}$/.test(value);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function readInt(value: string | undefined, fallback: number): number {
  const parsed = parseInt(value || "", 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

async function githubRequest<T>(
  endpoint: string,
  token: string,
  method: string = "GET",
  body?: unknown,
  attempt: number = 0
): Promise<T> {
  const response = await fetch(`https://api.github.com${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github.v3+json",
      "User-Agent": "backfill-duplicate-comments-script",
      ...(body !== undefined && { "Content-Type": "application/json" }),
    },
    ...(body !== undefined && { body: JSON.stringify(body) }),
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });

  if (!response.ok) {
    // One bounded retry for rate limiting / secondary limits.
    if ((response.status === 403 || response.status === 429) && attempt === 0) {
      const retryAfter = Number(response.headers.get("retry-after"));
      const delay = Number.isFinite(retryAfter) && retryAfter > 0
        ? Math.min(retryAfter * 1000, MAX_RETRY_DELAY_MS)
        : 1000;
      await sleep(delay);
      return githubRequest<T>(endpoint, token, method, body, attempt + 1);
    }

    throw new Error(
      `GitHub API request failed: ${response.status} ${response.statusText} (${method} ${endpoint})`
    );
  }

  return response.json() as Promise<T>;
}

async function triggerDedupeWorkflow(
  owner: string,
  repo: string,
  issueNumber: number,
  token: string,
  dryRun: boolean = true,
  ref: string = "main"
): Promise<void> {
  if (dryRun) {
    console.log(`[DRY RUN] Would trigger dedupe workflow for issue #${issueNumber}`);
    return;
  }

  await githubRequest(
    `/repos/${owner}/${repo}/actions/workflows/claude-dedupe-issues.yml/dispatches`,
    token,
    "POST",
    {
      ref,
      inputs: {
        issue_number: issueNumber.toString(),
      },
    }
  );
}

function isDuplicateDetectionComment(comment: GitHubComment): boolean {
  return (
    typeof comment.body === "string" &&
    comment.body.includes("Found") &&
    comment.body.includes("possible duplicate") &&
    comment.user?.type === "Bot"
  );
}

async function fetchIssuesInRange(
  owner: string,
  repo: string,
  token: string,
  minIssueNumber: number,
  maxIssueNumber: number
): Promise<GitHubIssue[]> {
  const allIssues: GitHubIssue[] = [];
  let page = 1;

  while (page <= MAX_PAGES) {
    const pageIssues = await githubRequest<GitHubIssue[]>(
      `/repos/${owner}/${repo}/issues?state=all&per_page=${PER_PAGE}&page=${page}&sort=created&direction=desc`,
      token
    );

    if (!Array.isArray(pageIssues) || pageIssues.length === 0) break;

    for (const issue of pageIssues) {
      if (issue.pull_request) continue;
      if (issue.number >= minIssueNumber && issue.number < maxIssueNumber) {
        allIssues.push(issue);
      }
    }

    const oldestIssueInPage = pageIssues[pageIssues.length - 1];
    if (oldestIssueInPage && oldestIssueInPage.number < minIssueNumber) {
      console.log(`[DEBUG] Oldest issue in page #${page} is #${oldestIssueInPage.number}, below minimum, stopping`);
      break;
    }

    if (pageIssues.length < PER_PAGE) break;
    page++;
  }

  return allIssues;
}

async function backfillDuplicateComments(): Promise<void> {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    throw new Error(`GITHUB_TOKEN environment variable is required

Usage:
  GITHUB_TOKEN=your_token bun run scripts/backfill-duplicate-comments.ts

Environment Variables:
  GITHUB_TOKEN - GitHub personal access token with repo and actions permissions (required)
  GITHUB_REPOSITORY_OWNER - Repository owner (default: ${DEFAULT_OWNER})
  GITHUB_REPOSITORY_NAME - Repository name (default: ${DEFAULT_REPO})
  DRY_RUN - Set to "false" to actually trigger workflows (default: true for safety)
  MIN_ISSUE_NUMBER - Only process issues with numbers >= this value (default: ${DEFAULT_MIN_ISSUE})
  MAX_ISSUE_NUMBER - Only process issues with numbers less than this value (default: ${DEFAULT_MAX_ISSUE})
  DISPATCH_REF - Git ref the workflow is dispatched on (default: main)`);
  }

  const owner = process.env.GITHUB_REPOSITORY_OWNER || DEFAULT_OWNER;
  const repo = process.env.GITHUB_REPOSITORY_NAME || DEFAULT_REPO;
  if (!isSafeSlug(owner) || !isSafeSlug(repo)) {
    throw new Error(`Invalid repository coordinates: ${owner}/${repo}`);
  }

  const dryRun = process.env.DRY_RUN !== "false";
  const maxIssueNumber = readInt(process.env.MAX_ISSUE_NUMBER, DEFAULT_MAX_ISSUE);
  const minIssueNumber = readInt(process.env.MIN_ISSUE_NUMBER, DEFAULT_MIN_ISSUE);
  const dispatchRef = process.env.DISPATCH_REF || "main";

  console.log(`[DEBUG] Repository: ${owner}/${repo}`);
  console.log(`[DEBUG] Dry run mode: ${dryRun}`);
  console.log(`[DEBUG] Looking at issues between #${minIssueNumber} and #${maxIssueNumber}`);

  const issues = await fetchIssuesInRange(owner, repo, token, minIssueNumber, maxIssueNumber);
  console.log(`[DEBUG] Found ${issues.length} issues in range`);

  let processed = 0;
  let candidateCount = 0;
  let triggeredCount = 0;

  for (const issue of issues) {
    processed++;

    try {
      const comments = await githubRequest<GitHubComment[]>(
        `/repos/${owner}/${repo}/issues/${issue.number}/comments?per_page=${PER_PAGE}`,
        token
      );

      const dupeDetectionComments = Array.isArray(comments)
        ? comments.filter(isDuplicateDetectionComment)
        : [];

      if (dupeDetectionComments.length > 0) {
        continue;
      }

      candidateCount++;
      await triggerDedupeWorkflow(owner, repo, issue.number, token, dryRun, dispatchRef);
      if (!dryRun) {
        console.log(`[SUCCESS] Triggered dedupe workflow for issue #${issue.number}`);
      }
      triggeredCount++;
    } catch (error) {
      console.error(`[ERROR] Failed to process issue #${issue.number}: ${error}`);
    }

    // Throttle workflow dispatches so the API is not overwhelmed.
    await sleep(TRIGGER_DELAY_MS);
  }

  console.log(
    `[DEBUG] Script completed. Processed ${processed} issues, found ${candidateCount} candidates without duplicate comments, ${dryRun ? "would trigger" : "triggered"} ${triggeredCount} workflows`
  );
}

backfillDuplicateComments().catch((error) => {
  console.error(`[FATAL] ${error instanceof Error ? error.message : error}`);
  process.exit(1);
});

// Make it a module
export {};
