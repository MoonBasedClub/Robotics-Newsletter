# News Scraper MVP

This repo now includes the backend foundation for the robotics and AI morning brief MVP:

- `api`: FastAPI service exposing dashboard-facing run endpoints
- `worker`: scheduled Python worker that discovers candidates, extracts article text, ranks stories, and generates concise outputs
- `db`: PostgreSQL for persisted runs, stories, and social posts

## Quick start

1. Copy `.env.example` to `.env`
2. Run `docker compose up --build`
3. Open `http://localhost:8000/health`
4. Open `http://localhost:8000/api/runs/latest`

## Current scope

The pipeline is intentionally lightweight for MVP:

- Google News RSS query discovery
- HTML extraction and article cleaning
- Heuristic ranking and categorization
- Deterministic summary and social-post generation

That gives us a stable end-to-end backend contract in Docker before we swap in richer LLM generation and more resilient source handling.
