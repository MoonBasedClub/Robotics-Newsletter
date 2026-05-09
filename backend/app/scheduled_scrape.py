import argparse
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.pipeline import _resolve_schedule, get_run_for_schedule, run_daily_digest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("news-scraper-scheduled")

DEFAULT_WINDOW_START_MINUTE = -5
DEFAULT_WINDOW_END_MINUTE = 20


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the idempotent scheduled news scrape when inside the configured local schedule window."
    )
    parser.add_argument(
        "--force-window",
        action="store_true",
        help="Bypass the local-time schedule window. Useful for manual GitHub workflow verification.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    tz = ZoneInfo(settings.scheduler_timezone)
    now = datetime.now(tz)

    if not args.force_window and not is_in_schedule_window(now):
        logger.info(
            "outside scheduled window now=%s timezone=%s target=%02d:%02d",
            now.isoformat(),
            settings.scheduler_timezone,
            settings.daily_run_hour,
            settings.daily_run_minute,
        )
        return 0

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        scheduled_for = _resolve_schedule(now.date().isoformat())
        existing = get_run_for_schedule(session, scheduled_for)
        if existing is not None:
            logger.info(
                "scheduled run already exists run_id=%s scheduled_for=%s status=%s",
                existing.id,
                scheduled_for.isoformat(),
                existing.status,
            )
            return 0

        run_id = run_daily_digest(session, date_override=now.date().isoformat(), force=False)
        logger.info(
            "scheduled scrape completed run_id=%s scheduled_for=%s",
            run_id,
            scheduled_for.isoformat(),
        )
        return 0
    except Exception:
        logger.exception("scheduled scrape failed")
        return 1
    finally:
        session.close()


def is_in_schedule_window(now: datetime) -> bool:
    settings = get_settings()
    scheduled_minutes = settings.daily_run_hour * 60 + settings.daily_run_minute
    current_minutes = now.hour * 60 + now.minute
    return (
        scheduled_minutes + DEFAULT_WINDOW_START_MINUTE
        <= current_minutes
        <= scheduled_minutes + DEFAULT_WINDOW_END_MINUTE
    )


if __name__ == "__main__":
    raise SystemExit(main())
