from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.services import create_demo_run


def run_daily_digest(session: Session, date_override: str | None = None) -> int:
    scheduled_for = _resolve_schedule(date_override)
    existing = session.scalar(
        select(models.Run).where(models.Run.scheduled_for == scheduled_for)
    )
    if existing is not None:
        return existing.id

    run = create_demo_run(session, scheduled_for=scheduled_for)
    return run.id


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
