import logging
from datetime import datetime
from time import sleep
from zoneinfo import ZoneInfo

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.pipeline import _resolve_schedule, get_run_for_schedule, run_daily_digest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("news-scraper-worker")


def execute_daily_run() -> None:
    session = SessionLocal()
    try:
        scheduled_for = _resolve_schedule(None)
        existing = get_run_for_schedule(session, scheduled_for)
        if existing is not None:
            logger.info(
                "scheduled daily digest already exists run_id=%s scheduled_for=%s status=%s",
                existing.id,
                scheduled_for.isoformat(),
                existing.status,
            )
            return

        run_id = run_daily_digest(session)
        logger.info(
            "completed scheduled daily digest run_id=%s scheduled_for=%s",
            run_id,
            scheduled_for.isoformat(),
        )
    except Exception:
        logger.exception("daily digest failed")
    finally:
        session.close()


def main() -> None:
    settings = get_settings()
    tz = ZoneInfo(settings.scheduler_timezone)
    now = datetime.now(tz)
    Base.metadata.create_all(bind=engine)

    if settings.run_on_startup:
        logger.info("RUN_ON_STARTUP enabled; executing a development startup scrape")
        execute_daily_run()

    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_listener(_log_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    trigger = CronTrigger(
        hour=settings.daily_run_hour,
        minute=settings.daily_run_minute,
        timezone=tz,
    )
    scheduler.add_job(
        execute_daily_run,
        trigger=trigger,
        id="daily-digest",
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60 * 60 * 2,
        replace_existing=True,
    )

    logger.info(
        "development scheduler started timezone=%s hour=%s minute=%s next_fire_time=%s",
        settings.scheduler_timezone,
        settings.daily_run_hour,
        settings.daily_run_minute,
        trigger.get_next_fire_time(None, now),
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("scheduler stopped")
        sleep(0.1)


def _log_job_event(event) -> None:
    if event.code == EVENT_JOB_MISSED:
        logger.warning("scheduled job missed job_id=%s scheduled_run_time=%s", event.job_id, event.scheduled_run_time)
    elif event.code == EVENT_JOB_ERROR:
        logger.error("scheduled job errored job_id=%s scheduled_run_time=%s", event.job_id, event.scheduled_run_time)
    elif event.code == EVENT_JOB_EXECUTED:
        logger.info("scheduled job executed job_id=%s scheduled_run_time=%s", event.job_id, event.scheduled_run_time)


if __name__ == "__main__":
    main()
