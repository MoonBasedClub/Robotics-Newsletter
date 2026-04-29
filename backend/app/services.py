from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas


def ensure_schema(session: Session) -> None:
    # Placeholder hook for startup validation if we later add migrations.
    session.execute(select(1))


def list_runs(session: Session) -> list[schemas.RunSummaryRead]:
    runs = session.scalars(
        select(models.Run)
        .options(
            selectinload(models.Run.selected_articles),
            selectinload(models.Run.social_posts),
        )
        .order_by(desc(models.Run.scheduled_for))
    ).all()
    return [_to_run_summary(run) for run in runs]


def get_run_by_id(session: Session, run_id: int) -> models.Run | None:
    return session.scalar(
        select(models.Run)
        .where(models.Run.id == run_id)
        .options(
            selectinload(models.Run.candidates),
            selectinload(models.Run.selected_articles),
            selectinload(models.Run.social_posts),
        )
    )


def get_latest_run(session: Session) -> models.Run | None:
    return session.scalar(
        select(models.Run)
        .options(
            selectinload(models.Run.candidates),
            selectinload(models.Run.selected_articles),
            selectinload(models.Run.social_posts),
        )
        .order_by(desc(models.Run.scheduled_for), desc(models.Run.id))
        .limit(1)
    )


def create_demo_run(session: Session, scheduled_for: datetime) -> models.Run:
    now = datetime.now(UTC)

    run = models.Run(
        scheduled_for=scheduled_for,
        started_at=now,
        completed_at=now,
        status="completed",
        query_set_version="v1",
        intro_summary=(
            "Robotics and AI coverage is clustering around industrial deployment, "
            "agent tooling, and commercialization pressure."
        ),
    )
    session.add(run)
    session.flush()

    candidate_specs = [
        ("Humanoid pilot expands in logistics test", "https://example.com/robotics-logistics", "example.com", 8.9, None),
        ("Frontier model startup lands enterprise pilot", "https://example.com/ai-enterprise-pilot", "example.com", 8.3, None),
        ("Warehouse autonomy vendor announces new fleet", "https://example.com/warehouse-fleet", "example.com", 7.8, None),
        ("Research roundup mirror", "https://example.com/mirror-roundup", "example.com", 4.1, "duplicate"),
    ]
    for title, url, domain, score, rejected_reason in candidate_specs:
        session.add(
            models.CandidateArticle(
                run_id=run.id,
                discovered_title=title,
                discovered_url=url,
                source_domain=domain,
                discovered_at=now,
                ranking_score=score,
                rejected_reason=rejected_reason,
            )
        )

    article_specs = [
        (
            1,
            "Robotics",
            "Humanoid pilot expands in logistics test",
            "Example Robotics",
            "Deployment is moving from demo theater into constrained, measurable workflows.",
            "Signals buyers are testing whether humanoids can clear narrow labor bottlenecks.",
            "https://example.com/robotics-logistics",
        ),
        (
            2,
            "AI Product",
            "Frontier model startup lands enterprise pilot",
            "Example AI",
            "The story is less about model novelty and more about who is willing to operationalize it now.",
            "Suggests enterprise AI budgets are consolidating around vendors with clearer workflow fit.",
            "https://example.com/ai-enterprise-pilot",
        ),
        (
            3,
            "Funding",
            "Warehouse autonomy vendor announces new fleet",
            "Automation Weekly",
            "Capital is still flowing into systems that can show hard throughput gains in physical operations.",
            "Reinforces that warehouse automation remains one of the fastest paths from AI narrative to ROI.",
            "https://example.com/warehouse-fleet",
        ),
    ]
    for rank, category, title, source_name, summary_short, why_it_matters, url in article_specs:
        session.add(
            models.SelectedArticle(
                run_id=run.id,
                canonical_url=url,
                title=title,
                source_name=source_name,
                author=None,
                published_at=now,
                cleaned_text_hash=None,
                category=category,
                summary_short=summary_short,
                why_it_matters=why_it_matters,
                article_rank=rank,
            )
        )

    posts = [
        "Robotics buyers are shifting from flashy prototypes to narrow workflow pilots with measurable value.",
        "Enterprise AI deals are increasingly won on deployment fit, not raw model mystique.",
        "Warehouse automation still looks like one of the clearest bridges from AI hype to operating leverage.",
    ]
    for ordinal, body in enumerate(posts, start=1):
        session.add(models.SocialPost(run_id=run.id, body=body, ordinal=ordinal))

    session.commit()
    session.refresh(run)
    return run


def _to_run_summary(run: models.Run) -> schemas.RunSummaryRead:
    return schemas.RunSummaryRead(
        id=run.id,
        scheduled_for=run.scheduled_for,
        completed_at=run.completed_at,
        status=run.status,
        intro_summary=run.intro_summary,
        story_count=len(run.selected_articles),
        social_post_count=len(run.social_posts),
    )
