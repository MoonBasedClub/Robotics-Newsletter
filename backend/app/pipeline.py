from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.discovery import discover_candidates
from app.extraction import cleaned_text_hash, extract_and_clean
from app.generation import generate_intro_summary, generate_social_posts, summarize_articles
from app.ranking import rank_and_select


def run_daily_digest(session: Session, date_override: str | None = None) -> int:
    scheduled_for = _resolve_schedule(date_override)
    existing = session.scalar(
        select(models.Run).where(models.Run.scheduled_for == scheduled_for)
    )
    if existing is not None:
        return existing.id

    now = datetime.now(UTC)
    run = models.Run(
        scheduled_for=scheduled_for,
        started_at=now,
        completed_at=None,
        status="running",
        query_set_version="v1",
        intro_summary=None,
    )
    session.add(run)
    session.flush()

    try:
        candidates = discover_candidates(now=now)
        candidate_records: dict[str, models.CandidateArticle] = {}
        for candidate in candidates:
            record = models.CandidateArticle(
                run_id=run.id,
                discovered_title=candidate.discovered_title,
                discovered_url=candidate.discovered_url,
                source_domain=candidate.source_domain,
                discovered_at=candidate.discovered_at,
                ranking_score=None,
                rejected_reason=None,
            )
            session.add(record)
            candidate_records[candidate.discovered_url] = record
        session.flush()

        extracted, extraction_failures = extract_and_clean(candidates)
        for candidate, reason in extraction_failures:
            record = candidate_records.get(candidate.discovered_url)
            if record is not None:
                record.rejected_reason = reason

        ranked, rejected_ranked = rank_and_select(extracted, now=now, limit=8)
        for ranked_article in ranked:
            record = candidate_records.get(ranked_article.article.discovered_url)
            if record is not None:
                record.ranking_score = ranked_article.ranking_score

        for article, reason in rejected_ranked:
            record = candidate_records.get(article.discovered_url)
            if record is not None:
                record.rejected_reason = reason

        summaries = summarize_articles(ranked)
        intro_summary = generate_intro_summary(summaries)
        social_posts = generate_social_posts(summaries)

        for ordinal, summary in enumerate(summaries, start=1):
            session.add(
                models.SelectedArticle(
                    run_id=run.id,
                    canonical_url=summary.article.article.canonical_url,
                    title=summary.article.article.title,
                    source_name=summary.article.article.source_name,
                    author=summary.article.article.author,
                    published_at=summary.article.article.published_at,
                    cleaned_text_hash=cleaned_text_hash(summary.article.article.cleaned_text),
                    category=summary.article.category,
                    summary_short=summary.summary_short,
                    why_it_matters=summary.why_it_matters,
                    article_rank=ordinal,
                )
            )

        for post in social_posts:
            session.add(
                models.SocialPost(run_id=run.id, body=post.body, ordinal=post.ordinal)
            )

        run.intro_summary = intro_summary
        run.status = "completed" if summaries else "partial"
        run.completed_at = datetime.now(UTC)
        session.commit()
        return run.id
    except Exception:
        run.status = "failed"
        run.completed_at = datetime.now(UTC)
        session.commit()
        raise


def _resolve_schedule(date_override: str | None) -> datetime:
    settings = get_settings()
    tz = ZoneInfo(settings.scheduler_timezone)

    if date_override:
        parsed = datetime.fromisoformat(date_override)
        if parsed.tzinfo is None:
            local_date = parsed.date()
        else:
            local_date = parsed.astimezone(tz).date()
    else:
        local_date = datetime.now(tz).date()

    scheduled_local = datetime(
        year=local_date.year,
        month=local_date.month,
        day=local_date.day,
        hour=settings.daily_run_hour,
        minute=settings.daily_run_minute,
        tzinfo=tz,
    )
    return scheduled_local.astimezone(UTC)
