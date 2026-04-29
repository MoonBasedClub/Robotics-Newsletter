# Robotics + AI Morning Newsletter Dashboard MVP

## Summary

Build a greenfield Dockerized app with a `Next.js` dashboard and a Python ingestion pipeline. Every day at **9:00 AM America/New_York**, the pipeline discovers fresh robotics and AI stories from the open web, cleans and deduplicates them, selects the **top 5-8 stories**, generates ultra-condensed AI summaries plus **3-5 copy-paste-ready X posts**, stores the run, and exposes it to the dashboard. No auth or hardening is included in MVP beyond basic container/env configuration.

## Implementation Changes

### 1. System shape
- Use `docker-compose` with three services:
  - `web`: Next.js app for dashboard UI
  - `worker`: Python service for discovery, scraping, processing, summarization, and generation
  - `db`: Postgres for archived runs, articles, summaries, and social outputs
- Run the schedule inside the Python worker using a timezone-aware scheduler set to `America/New_York`.
- Expose a small internal API from the Python service or let Next.js read from Postgres through a server-side data layer. Default to a small Python API so the pipeline contract stays explicit.

### 2. Daily pipeline behavior
- Trigger one `daily run` at 9:00 AM EST/EDT.
- Discovery step:
  - Use keyword-driven open-web discovery with a controlled implementation, not arbitrary crawling.
  - Default source discovery to **Google News RSS / news-search style queries** for robotics and AI topics, then resolve candidate links to original articles.
  - Seed query groups:
    - `robotics`, `humanoid robots`, `autonomous systems`, `warehouse robotics`, `industrial robotics`
    - `artificial intelligence`, `foundation models`, `AI agents`, `machine learning`, `AI startups`
- Candidate filtering:
  - Keep only items published within the last 24-36 hours.
  - Normalize URLs and remove duplicates by canonical URL, title similarity, and domain/article slug heuristics.
  - Exclude low-signal content such as press-release mirrors, roundup duplicates, and pages with insufficient extractable body text.
- Extraction step:
  - Fetch the article page and extract `title`, `source`, `author if present`, `published_at`, `canonical_url`, and cleaned body text.
  - Store extraction failures but do not fail the whole run because of individual articles.
- Ranking step:
  - Score candidates on topic relevance, recency, source quality, and novelty against already-selected stories.
  - Select the best **5-8** articles for the final brief.
- AI generation step:
  - For each selected article, generate:
    - `ultra-short summary` optimized for a fast morning read
    - `why it matters` sentence
    - `category` such as `Robotics`, `AI Research`, `AI Product`, `Funding`, `Policy`
  - Generate a stitched `daily brief intro` summarizing the whole morning in a few lines.
  - Generate **3-5 standalone X posts**, each concise and directly copy-pasteable.
- Persistence step:
  - Save the full run, selected articles, per-article outputs, and social outputs for archive/history.

### 3. Dashboard UX
- Default landing page shows the **latest morning run**.
- Main sections:
  - `Morning Brief`: date, run status, short intro, total selected stories
  - `Top Stories`: 5-8 cards with headline, source, published time, compressed summary, why-it-matters, and outbound link
  - `Social Posts`: 3-5 copy blocks with one-click copy interaction
  - `Archive`: prior runs listed by date with ability to open a previous day
- Keep the interface optimized for speed and scanning, not deep reading.
- No editing workflow in MVP; generated content is read-only.
- No auth, user accounts, or personalization in MVP.

### 4. Data model and interfaces
- Core persisted entities:
  - `Run`: id, scheduled_for, started_at, completed_at, status, query_set_version, intro_summary
  - `CandidateArticle`: run_id, discovered_title, discovered_url, source_domain, discovered_at, ranking_score, rejected_reason
  - `SelectedArticle`: run_id, canonical_url, title, source_name, author, published_at, cleaned_text_hash, category, summary_short, why_it_matters, article_rank
  - `SocialPost`: run_id, body, ordinal
- Internal pipeline interface:
  - `run_daily_digest(date_override?: string) -> run_id`
  - `discover_candidates(run_id) -> candidates[]`
  - `extract_and_clean(candidates) -> normalized_articles[]`
  - `rank_and_select(articles, limit=8) -> selected_articles[]`
  - `summarize_articles(selected_articles) -> article_summaries[]`
  - `generate_social_posts(run_context) -> posts[]`
- External app interface:
  - `GET /api/runs/latest`
  - `GET /api/runs/:id`
  - `GET /api/runs`
- Keep OpenAI provider config-driven via env vars; do not hardcode model names in the architecture. One summarization model setting and one social-generation setting are enough for MVP.

## Test Plan

- Scheduler test: verify the worker schedules at **9:00 AM America/New_York** across DST boundaries.
- Discovery test: verify query execution returns candidates for both robotics and AI topic sets.
- Dedup test: verify mirrored/reposted stories collapse to one canonical article.
- Extraction test: verify article body cleaning succeeds on representative news-site HTML and fails gracefully on bad pages.
- Ranking test: verify the pipeline returns no more than 8 selected stories and prioritizes recency plus relevance.
- Summarization test: verify every selected article produces a short summary and why-it-matters field, even when source text is noisy.
- Social generation test: verify exactly 3-5 X posts are created and remain short enough for practical copy/paste use.
- Persistence test: verify a completed run can be reloaded from the dashboard archive with all linked stories and posts.
- End-to-end test: execute one full mocked daily run in Docker and verify latest dashboard data renders without manual intervention.

## Assumptions and Defaults

- Greenfield build; no existing repo or schema is being integrated.
- `Custom Python` is the ingestion path for MVP; Apify is deferred unless certain sources prove too brittle.
- `Dashboard only` is the MVP output; no email sending is included.
- History is required, so Postgres is preferred over SQLite.
- Open-web discovery is implemented as search-driven link discovery plus article-page extraction, not unrestricted crawling.
- Security, auth, rate-limiting, editorial approval, and admin tooling are explicitly out of scope for MVP.
- If a run partially fails, the dashboard should still show the best completed output for that day with run-status visibility.
