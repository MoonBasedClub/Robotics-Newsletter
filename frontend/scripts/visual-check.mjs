import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const run = {
  id: 1,
  scheduled_for: "2026-04-30T13:00:00Z",
  started_at: "2026-04-30T13:00:02Z",
  completed_at: "2026-04-30T13:03:15Z",
  status: "completed",
  query_set_version: "v1",
  intro_summary:
    "Today's brief clusters around warehouse autonomy, fast-moving AI product releases, and policy pressure on frontier systems.",
  selected_articles: [
    {
      id: 10,
      canonical_url: "https://example.com/robots-warehouse",
      title: "Humanoid robots enter warehouse pilot",
      source_name: "example.com",
      author: "Jane Reporter",
      published_at: "2026-04-30T12:15:00Z",
      category: "Robotics",
      summary_short:
        "Operators are testing humanoid robots in live warehouse workflows after months of controlled demos.",
      why_it_matters:
        "Signals where physical automation is finding operational pull instead of demo-only attention.",
      article_rank: 1
    },
    {
      id: 11,
      canonical_url: "https://example.com/ai-product",
      title: "AI coding assistant ships autonomous review mode",
      source_name: "example.com",
      author: null,
      published_at: "2026-04-30T11:10:00Z",
      category: "AI Product",
      summary_short:
        "A new release adds asynchronous review flows for teams managing larger codebases.",
      why_it_matters:
        "Shows AI product work moving from chat surfaces toward persistent software operations.",
      article_rank: 2
    },
    {
      id: 12,
      canonical_url: "https://example.com/policy",
      title: "Regulators propose new reporting rules for model incidents",
      source_name: "example.com",
      author: "Policy Desk",
      published_at: null,
      category: "Policy",
      summary_short:
        "The draft rules would require faster disclosure of major safety and reliability incidents.",
      why_it_matters:
        "Raises the compliance floor for organizations deploying frontier models in production.",
      article_rank: 3
    }
  ],
  social_posts: [
    {
      id: 4,
      body:
        "Robotics: Humanoid robots enter warehouse pilot. The signal is less about novelty and more about live operational pull.",
      ordinal: 1
    },
    {
      id: 5,
      body:
        "AI product teams are pushing assistants into review and operations workflows, not just chat. That is where adoption gets sticky.",
      ordinal: 2
    }
  ],
  candidates: [
    {
      id: 21,
      discovered_title: "Humanoid robots enter warehouse pilot",
      discovered_url: "https://example.com/robots-warehouse",
      source_domain: "example.com",
      discovered_at: "2026-04-30T12:15:00Z",
      ranking_score: 8.7,
      rejected_reason: null
    },
    {
      id: 22,
      discovered_title: "Duplicate robotics story",
      discovered_url: "https://example.com/duplicate",
      source_domain: "example.com",
      discovered_at: "2026-04-30T12:00:00Z",
      ranking_score: 5.3,
      rejected_reason: "duplicate_title"
    }
  ]
};

const runSummary = {
  id: 1,
  scheduled_for: run.scheduled_for,
  completed_at: run.completed_at,
  status: run.status,
  intro_summary: run.intro_summary,
  story_count: run.selected_articles.length,
  social_post_count: run.social_posts.length
};

await mkdir("artifacts", { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });

await page.route("**/api/runs/latest", (route) => route.fulfill({ json: { data: run } }));
await page.route("**/api/runs/1", (route) => route.fulfill({ json: { data: run } }));
await page.route("**/api/runs", (route) =>
  route.fulfill({ json: { data: [runSummary], meta: { total: 1 } } })
);

await page.goto("http://localhost:5173", { waitUntil: "networkidle" });
await page.getByRole("heading", { name: "Thursday, April 30" }).waitFor();
await page.screenshot({ path: "artifacts/dashboard-desktop.png", fullPage: true });

await page.setViewportSize({ width: 375, height: 1000 });
await page.goto("http://localhost:5173", { waitUntil: "networkidle" });
await page.getByRole("heading", { name: "Thursday, April 30" }).waitFor();
await page.screenshot({ path: "artifacts/dashboard-mobile.png", fullPage: true });

await browser.close();
