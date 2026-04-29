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
