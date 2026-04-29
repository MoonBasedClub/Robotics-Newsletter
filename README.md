# News Scraper MVP

This repo now includes the first backend foundation for the robotics and AI morning brief MVP:

- `api`: FastAPI service exposing dashboard-facing run endpoints
- `worker`: scheduled Python worker that creates a valid daily run shape
- `db`: PostgreSQL for persisted runs, stories, and social posts

## Quick start

1. Copy `.env.example` to `.env`
2. Run `docker compose up --build`
3. Open `http://localhost:8000/health`
4. Open `http://localhost:8000/api/runs/latest`

## Current scope

The worker currently creates a demo run so the dashboard contract is stable while the real discovery, extraction, ranking, and LLM generation steps are implemented.
