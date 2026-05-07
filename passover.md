# RSS/Google News Fix Handoff

## Goal

Fix Google News RSS discovery so candidates become original publisher URLs before extraction. Previous runs stored `source_domain = news.google.com`, fetched wrapper pages, rejected everything as `insufficient_text`, and produced no selected articles/posts.

## Files Changed

- `backend/app/discovery.py`
- `backend/tests/test_pipeline_quality.py`
- `backend/app/extraction.py`
- `backend/app/generation.py`

## RSS Fix State

`discovery.py` now has layered Google News resolution:

- Existing `?url=` / `?u=` query-param wrappers still resolve directly.
- Base64-ish Google News IDs are decoded locally when they embed an `https://...` URL.
- Opaque `CB...` IDs now fetch the Google wrapper HTML using a browser-ish UA: `Mozilla/5.0 (compatible; news-scraper/0.1)`.
- Wrapper HTML is parsed with BeautifulSoup:
  - Prefer `c-wiz[data-p]`.
  - Parse its `%.@.` payload.
  - Convert that into an `Fbv4je` batch payload.
  - Extract `garturlres` publisher URL from the response.
- Fallback exists for `[data-n-a-id][data-n-a-ts][data-n-a-sg]`.
- Unresolved Google News links are skipped and logged with: `skipped %s unresolved Google News RSS links`.
- `_default_fetch` now uses the browser-ish UA.

## Important Live Verification Already Done

A live local resolver probe succeeded:

```text
google_domain: news.google.com
resolved: https://techcrunch.com/2026/05/06/khosla-backed-robotics-startup-genesis-ai-has-gone-full-stack-demo-shows/
resolved_domain: techcrunch.com
```

That proves the current code can resolve at least one current Google News RSS `CB...` link to the publisher URL.

## Tests Added

In `backend/tests/test_pipeline_quality.py`:

- Old `?url=` Google News wrapper still works.
- Encoded Google News article links with embedded publisher URL resolve.
- Unresolvable Google News links are skipped.
- Opaque `CB...` IDs use mocked wrapper HTML + mocked batch response.
- Old and encoded wrappers dedupe by normalized publisher URL.

## Other Cleanup

`extraction.py`:

- Added `Tag` narrowing and `_string_attr()` helper to satisfy Pyright for BeautifulSoup calls.
- Behavior unchanged except safer metadata attr handling.

`generation.py`:

- Fixed Pyright warning where `api_key.strip()` was called after a bool helper that did not narrow `None`.
- Added `_normalized_openai_api_key()` and uses it before creating OpenAI client.

## Verification Completed

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

Result: `20 passed, 4 warnings`.

```powershell
npx pyright
```

Result: `0 errors, 0 warnings, 0 informations`.

`backend\.venv` was synced with requirements; `openai==2.8.1` installed.

Docker env check previously showed:

- `has_openai_api_key: True`
- summarization/social models set to `gpt-5.4-mini`

## Docker/Rebuild Note

No rebuild is needed for the RSS code changes because `docker-compose.yml` mounts:

```yaml
./backend:/app
```

into the worker/api containers. The running worker will see `backend/app/discovery.py` changes immediately. Rebuild is only needed for baked image changes like `requirements.txt` or `Dockerfile`.

## Where We Stopped

I started a manual scrape:

```powershell
docker compose exec worker python -m app.manual_scrape
```

It was interrupted after about 4 minutes by the user. It may have partially executed in the container. Before rerunning, check latest runs/counts or just run a fresh manual scrape since `manual_scrape` forces a new run.

## Next Recommended Command

Run:

```powershell
docker compose exec worker python -m app.manual_scrape
```

Then inspect latest run diagnostics:

- candidates > 0
- candidate `source_domain` should be publisher domains, not `news.google.com`
- selected_articles > 0 if extraction/ranking succeeds
- social_posts > 0 if summaries exist, using OpenAI or deterministic fallback
