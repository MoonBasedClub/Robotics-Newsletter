# API Handoff: Morning Brief Dashboard

## Business Context
The backend powers a robotics and AI morning brief dashboard. A scheduled worker discovers open-web stories, extracts article text, ranks the best stories, generates concise summaries plus social posts, and stores each run in Postgres. The frontend should optimize for fast scanning of the latest run, with an archive for previous runs.

## Endpoints

### GET /health
- **Purpose**: Confirms the API process is running.
- **Auth**: Public.
- **Request**: None.
- **Response** (success):
  ```json
  {
    "data": {
      "status": "ok"
    }
  }
  ```
- **Response** (error): Standard HTTP/network failure if the API is unavailable.
- **Notes**: Use for local smoke checks only; this does not prove the worker has produced a run.

### GET /api/runs
- **Purpose**: Lists archived runs newest-first for the dashboard archive.
- **Auth**: Public.
- **Request**: None.
- **Response** (success):
  ```json
  {
    "data": [
      {
        "id": 1,
        "scheduled_for": "2026-04-30T13:00:00Z",
        "completed_at": "2026-04-30T13:03:15Z",
        "status": "completed",
        "intro_summary": "Today's brief clusters around AI Product, Robotics...",
        "story_count": 8,
        "social_post_count": 5
      }
    ],
    "meta": {
      "total": 1
    }
  }
  ```
- **Response** (error): No domain-specific errors currently returned.
- **Notes**: No pagination yet. If the list is empty, `data` is `[]` and `meta.total` is `0`.

### GET /api/runs/latest
- **Purpose**: Returns the latest run with selected stories, social posts, and candidate diagnostics.
- **Auth**: Public.
- **Request**: None.
- **Response** (success):
  ```json
  {
    "data": {
      "id": 1,
      "scheduled_for": "2026-04-30T13:00:00Z",
      "started_at": "2026-04-30T13:00:02Z",
      "completed_at": "2026-04-30T13:03:15Z",
      "status": "completed",
      "query_set_version": "v1",
      "intro_summary": "Today's brief clusters around AI Product, Robotics...",
      "selected_articles": [
        {
          "id": 10,
          "canonical_url": "https://example.com/story",
          "title": "Humanoid robots enter warehouse pilot",
          "source_name": "example.com",
          "author": "Jane Reporter",
          "published_at": "2026-04-30T12:15:00Z",
          "category": "Robotics",
          "summary_short": "Humanoid robots enter warehouse pilot: Operators are testing...",
          "why_it_matters": "Shows where physical automation is finding real operational pull instead of demo-only attention.",
          "article_rank": 1
        }
      ],
      "social_posts": [
        {
          "id": 4,
          "body": "Robotics: Humanoid robots enter warehouse pilot. Shows where physical automation...",
          "ordinal": 1
        }
      ],
      "candidates": [
        {
          "id": 21,
          "discovered_title": "Humanoid robots enter warehouse pilot",
          "discovered_url": "https://example.com/story",
          "source_domain": "example.com",
          "discovered_at": "2026-04-30T12:15:00Z",
          "ranking_score": 8.7,
          "rejected_reason": null
        }
      ]
    }
  }
  ```
- **Response** (error):
  ```json
  {
    "detail": "No runs available"
  }
  ```
- **Notes**: Returns `404` until the worker has saved at least one run.

### GET /api/runs/{run_id}
- **Purpose**: Returns a specific run for archive detail views.
- **Auth**: Public.
- **Request**:
  ```json
  {
    "run_id": "integer path parameter"
  }
  ```
- **Response** (success): Same shape as `GET /api/runs/latest`.
- **Response** (error):
  ```json
  {
    "detail": "Run not found"
  }
  ```
- **Notes**: Use run IDs from `GET /api/runs`.

## Data Models / DTOs

```typescript
type RunStatus = 'running' | 'completed' | 'partial' | 'failed';

type ArticleCategory =
  | 'Robotics'
  | 'AI Research'
  | 'AI Product'
  | 'Funding'
  | 'Policy';

interface DataEnvelope<T> {
  data: T;
}

interface ListEnvelope<T> {
  data: T[];
  meta: {
    total: number;
  };
}

interface RunSummary {
  id: number;
  scheduled_for: string;
  completed_at: string | null;
  status: RunStatus;
  intro_summary: string | null;
  story_count: number;
  social_post_count: number;
}

interface RunDetail {
  id: number;
  scheduled_for: string;
  started_at: string;
  completed_at: string | null;
  status: RunStatus;
  query_set_version: string;
  intro_summary: string | null;
  selected_articles: SelectedArticle[];
  social_posts: SocialPost[];
  candidates: CandidateArticle[];
}

interface SelectedArticle {
  id: number;
  canonical_url: string;
  title: string;
  source_name: string;
  author: string | null;
  published_at: string | null;
  category: ArticleCategory;
  summary_short: string;
  why_it_matters: string;
  article_rank: number;
}

interface SocialPost {
  id: number;
  body: string;
  ordinal: number;
}

interface CandidateArticle {
  id: number;
  discovered_title: string;
  discovered_url: string;
  source_domain: string;
  discovered_at: string;
  ranking_score: number | null;
  rejected_reason: string | null;
}
```

## Enums & Constants

| Value | Meaning | Display Label |
|-------|---------|---------------|
| `running` | Worker started a run that has not completed yet | Running |
| `completed` | Run produced at least one selected story | Completed |
| `partial` | Run completed but selected no qualifying stories | Partial |
| `failed` | Run raised an unhandled error | Failed |
| `duplicate` | Candidate matched an already-seen canonical URL or content hash | Duplicate |
| `duplicate_title` | Candidate title was too similar to an already-ranked story | Similar story |
| `below_cutoff` | Candidate ranked below the selected story limit | Not selected |
| `insufficient_text` | Extracted article body was too short to summarize | Too little text |
| `extraction_failed` | Article page fetch or parse failed | Extraction failed |

## Validation Rules
The current API is read-only. Frontend validation is limited to treating `run_id` as a positive integer and handling nullable timestamp, author, intro, ranking score, and rejection fields.

## Business Logic & Edge Cases
- The latest run is selected by scheduled time, then ID.
- Runs are scheduled for 9:00 AM America/New_York and stored as UTC timestamps.
- The worker can save `partial` runs; the frontend should still render the run shell, intro text, diagnostics, and empty story/post states.
- `selected_articles` is ordered by `article_rank`; `social_posts` is ordered by `ordinal`.
- `candidates` is diagnostic data. It is useful for an admin/debug view but should not dominate the main reader experience.
- There is no auth, pagination, mutation endpoint, or real-time update channel in the MVP backend.

## Integration Notes
- **Recommended flow**: Fetch `/api/runs/latest` for the default dashboard, fetch `/api/runs` for archive navigation, then fetch `/api/runs/{run_id}` when opening an archived run.
- **Optimistic UI**: Not applicable because the API is read-only.
- **Caching**: Safe to cache `/api/runs` and run detail responses briefly in the frontend. Refresh manually or on page focus if the worker may have just completed.
- **Real-time**: Not available. Polling `/api/runs/latest` every 30-60 seconds is reasonable only while a run is expected or `status` is `running`.

## Test Scenarios
1. **Latest run happy path**: `/api/runs/latest` returns `200`, one run detail, stories sorted by `article_rank`, and social posts sorted by `ordinal`.
2. **Empty backend**: `/api/runs` returns an empty list and `/api/runs/latest` returns `404` with `detail: "No runs available"`.
3. **Archived run happy path**: User selects a run from `/api/runs`; `/api/runs/{id}` returns the same detail shape as latest.
4. **Missing archive run**: `/api/runs/999` returns `404` with `detail: "Run not found"`.
5. **Partial run**: A run with `status: "partial"` and empty story/post arrays still renders a useful empty state.
6. **Nullable fields**: Frontend tolerates `author`, `published_at`, `completed_at`, `intro_summary`, `ranking_score`, and `rejected_reason` as `null`.

## Open Questions / TODOs
- Pagination or date filtering for `/api/runs` will be needed once the archive grows.
- Error responses currently use FastAPI's default `detail` shape, not the richer `{ error: { code, message } }` envelope.
- A frontend-facing manual trigger endpoint does not exist yet.
