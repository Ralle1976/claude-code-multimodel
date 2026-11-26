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

interface GitHubReaction {
  user: { id: number } | null;
  content: string;
}

const REQUEST_TIMEOUT_MS = 30000;
const MAX_PAGES = 20;
const PER_PAGE = 100;
// Bounds for the optional single retry on rate limiting.
const MAX_RETRY_DELAY_MS = 60000;
const DEFAULT_OWNER = "anthropics";
const DEFAULT_REPO = "claude-code";

function isSafeSlug(value: string): boolean {
  return /^[A-Za-z0-9_.-]{1,100}$/.test(value);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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
      "User-Agent": "auto-close-duplicates-script",
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

function extractDuplicateIssueNumber(commentBody: string): number | null {
  // Try to match #123 format first
  let match = commentBody.match(/#(\d+)/);
  if (match) {
    return parseInt(match[1], 10);
  }

  // Try to match GitHub issue URL format: https://github.com/owner/repo/issues/123
  match = commentBody.match(/github\.com\/[^/]+\/[^/]+\/issues\/(\d+)/);
  if (match) {
    return parseInt(match[1], 10);
  }

  return null;
}

function isDuplicateDetectionComment(comment: GitHubComment): boolean {
  return (
    typeof comment.body === "string" &&
    comment.body.includes("Found") &&
    comment.body.includes("possible duplicate") &&
    comment.user?.type === "Bot"
  );
}

async function closeIssueAsDuplicate(
  owner: string,
  repo: string,
  issueNumber: number,
  duplicateOfNumber: number,
  token: string
): Promise<void> {
  await githubRequest(
    `/repos/${owner}/${repo}/issues/${issueNumber}`,
    token,
    "PATCH",
    {
      state: "closed",
      state_reason: "duplicate",
    }
  );

  // POST /labels adds instead of replacing, so existing triage labels survive.
  await githubRequest(
    `/repos/${owner}/${repo}/issues/${issueNumber}/labels`,
    token,
    "POST",
    { labels: ["duplicate"] }
  );

  await githubRequest(
    `/repos/${owner}/${repo}/issues/${issueNumber}/comments`,
    token,
    "POST",
    {
      body: `This issue has been automatically closed as a duplicate of #${duplicateOfNumber}.

If this is incorrect, please re-open this issue or create a new one.

🤖 Generated with [Claude Code](https://claude.ai/code)`,
    }
  );
}

async function fetchOpenIssues(owner: string, repo: string, token: string): Promise<GitHubIssue[]> {
  const threeDaysAgo = new Date();
  threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

  const found: GitHubIssue[] = [];
  let page = 1;

  while (page <= MAX_PAGES) {
    const pageIssues = await githubRequest<GitHubIssue[]>(
      `/repos/${owner}/${repo}/issues?state=open&per_page=${PER_PAGE}&page=${page}`,
      token
    );

    if (!Array.isArray(pageIssues) || pageIssues.length === 0) break;

    // The /issues endpoint also returns pull requests - closing those as
    // "duplicate" would be wrong.
    for (const issue of pageIssues) {
      if (issue.pull_request) continue;
      if (new Date(issue.created_at) <= threeDaysAgo) {
        found.push(issue);
      }
    }

    if (pageIssues.length < PER_PAGE) break;
    page++;
  }

  return found;
}

async function shouldClose(
  owner: string,
  repo: string,
  issue: GitHubIssue,
  token: string
): Promise<number | null> {
  const comments = await githubRequest<GitHubComment[]>(
    `/repos/${owner}/${repo}/issues/${issue.number}/comments?per_page=${PER_PAGE}`,
    token
  );

  if (!Array.isArray(comments)) return null;

  const dupeComments = comments.filter(isDuplicateDetectionComment);
  if (dupeComments.length === 0) return null;

  const lastDupeComment = dupeComments[dupeComments.length - 1];
  const dupeCommentDate = new Date(lastDupeComment.created_at);

  const threeDaysAgo = new Date();
  threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
  if (dupeCommentDate > threeDaysAgo) return null;

  const commentsAfterDupe = comments.filter(
    (comment) => new Date(comment.created_at) > dupeCommentDate
  );
  if (commentsAfterDupe.length > 0) return null;

  const reactions = await githubRequest<GitHubReaction[]>(
    `/repos/${owner}/${repo}/issues/comments/${lastDupeComment.id}/reactions?per_page=${PER_PAGE}`,
    token
  );

  const authorThumbsDown = Array.isArray(reactions) && reactions.some(
    (reaction) =>
      reaction.content === "-1" && reaction.user?.id === issue.user.id
  );
  if (authorThumbsDown) return null;

  const duplicateIssueNumber = extractDuplicateIssueNumber(lastDupeComment.body);
  if (!duplicateIssueNumber || duplicateIssueNumber === issue.number) return null;

  return duplicateIssueNumber;
}

async function autoCloseDuplicates(): Promise<void> {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    throw new Error("GITHUB_TOKEN environment variable is required");
  }

  const owner = process.env.GITHUB_REPOSITORY_OWNER || DEFAULT_OWNER;
  const repo = process.env.GITHUB_REPOSITORY_NAME || DEFAULT_REPO;

  // owner/repo werden in URL-Pfade interpoliert - '/' oder '..' wuerden
  // stillschweigend einen anderen API-Endpunkt ansprechen.
  if (!isSafeSlug(owner) || !isSafeSlug(repo)) {
    throw new Error(`Invalid repository coordinates: ${owner}/${repo}`);
  }

  console.log(`[DEBUG] Repository: ${owner}/${repo}`);

  const issues = await fetchOpenIssues(owner, repo, token);
  console.log(`[DEBUG] Found ${issues.length} open issues older than 3 days`);

  let processed = 0;
  let candidateCount = 0;

  for (const issue of issues) {
    processed++;
    try {
      const duplicateOf = await shouldClose(owner, repo, issue, token);
      if (duplicateOf === null) {
        console.log(`[DEBUG] Issue #${issue.number} - no auto-close (${processed}/${issues.length})`);
        continue;
      }

      candidateCount++;
      console.log(`[INFO] Auto-closing issue #${issue.number} as duplicate of #${duplicateOf}`);
      await closeIssueAsDuplicate(owner, repo, issue.number, duplicateOf, token);
      console.log(`[SUCCESS] Closed issue #${issue.number} as duplicate of #${duplicateOf}`);
    } catch (error) {
      console.error(`[ERROR] Failed to process issue #${issue.number}: ${error}`);
    }
  }

  console.log(
    `[DEBUG] Script completed. Processed ${processed} issues, closed ${candidateCount} duplicates`
  );
}

autoCloseDuplicates().catch((error) => {
  console.error(`[FATAL] ${error instanceof Error ? error.message : error}`);
  process.exit(1);
});

// Make it a module
export {};
