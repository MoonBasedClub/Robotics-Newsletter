# News Scraper MVP

This repo now includes the backend foundation for the robotics and AI morning brief MVP:

- `api`: FastAPI service exposing dashboard-facing run endpoints
- `worker`: scheduled Python worker that discovers candidates, extracts article text, ranks stories, and generates concise outputs
- `db`: PostgreSQL for persisted runs, stories, and social posts
- `frontend`: Vite-powered React dashboard for the latest brief, story cards, social posts, and archive history

## Tech stack

### Frontend

- **Runtime/build tool**: Vite
- **UI framework**: React
- **Language**: TypeScript
- **Routing**: React Router
- **Server state**: TanStack Query
- **Styling**: Tokenized CSS with CSS variables for light and dark themes
- **Icons**: lucide-react
- **Date formatting**: date-fns

### Backend

- **API framework**: FastAPI
- **Language**: Python
- **Validation/serialization**: Pydantic
- **Database ORM**: SQLAlchemy
- **Database**: PostgreSQL 16
- **Worker/runtime**: Python scheduled worker
- **Testing**: pytest

### Local infrastructure

- **Container orchestration**: Docker Compose
- **API dev server**: Uvicorn with reload
- **Frontend dev proxy**: Vite proxies `/api` and `/health` to `http://localhost:8000`

## Quick start

1. Copy `.env.example` to `.env`
2. Run `docker compose up --build`
3. Open the dashboard at `http://localhost:5173`
4. Open the API health check at `http://localhost:8000/health`
5. Open the latest run payload at `http://localhost:8000/api/runs/latest`

Docker Compose starts:

- `frontend` on `http://localhost:5173`
- `api` on `http://localhost:8000`
- `worker` for local development experiments with scheduled scraping/generation
- `db` on local port `5432`

Inside Docker, the frontend dev server proxies API calls to `http://api:8000`. Outside Docker, local Vite development proxies to `http://localhost:8000`.

## Production scheduling

Production 9:00 AM America/New_York scraping is handled by GitHub Actions in `.github/workflows/daily-scrape.yml`. The workflow runs against the shared `DATABASE_URL` secret, which should point to Supabase or another reachable Postgres database.

Local Docker scheduling is development-only because it depends on the host machine staying awake. Keep `RUN_ON_STARTUP=false` locally unless you intentionally want the worker to scrape as soon as the container starts.

## Manual scraping

To manually start a fresh scrape without waiting for the scheduler, run:

```bash
docker compose exec worker python -m app.manual_scrape
```

To run a fresh scrape for a specific local schedule date, run:

```bash
docker compose exec worker python -m app.manual_scrape --date 2026-05-03
```

Manual scrapes intentionally force a new run, even if a partial or completed run already exists for that date. The dashboard treats the newest run for a scheduled date as latest, so this is the simplest developer-only refresh path without adding admin UI.

If the dashboard shows a partial run message, the backend saved the run shell and diagnostics but did not produce selected stories or social posts. That usually means discovery or extraction found candidates, but the later selection/generation stages did not produce final output.

## OpenAI generation

The backend uses OpenAI for article summaries, the dashboard intro, and social posts when `OPENAI_API_KEY` is configured:

- `OPENAI_API_KEY` is the secret credential the backend will use when it starts calling OpenAI.
- `OPENAI_SUMMARIZATION_MODEL` controls article summaries, "why it matters" text, and the run intro. The MVP default is `gpt-5.4-mini`.
- `OPENAI_SOCIAL_MODEL` controls copy-ready social post generation. The MVP default is `gpt-5.4-mini`.

Generation uses the OpenAI Responses API with structured outputs so the backend receives predictable fields to persist. If the API key is missing or an OpenAI call fails, the scraper falls back to deterministic local generation instead of failing the whole run.

## Frontend development

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Keep the backend running on `http://localhost:8000` so the Vite proxy can reach the API.

## Current scope

The pipeline is intentionally lightweight for MVP:

- Google News RSS query discovery
- HTML extraction and article cleaning
- Heuristic ranking and categorization
- OpenAI-backed summary and social-post generation with deterministic fallback

That gives us a stable end-to-end backend contract in Docker before we swap in richer LLM generation and more resilient source handling.
