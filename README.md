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
- `worker` for scheduled scraping/generation
- `db` on local port `5432`

Inside Docker, the frontend dev server proxies API calls to `http://api:8000`. Outside Docker, local Vite development proxies to `http://localhost:8000`.

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
- Deterministic summary and social-post generation

That gives us a stable end-to-end backend contract in Docker before we swap in richer LLM generation and more resilient source handling.
