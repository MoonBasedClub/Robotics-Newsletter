import logging
from time import sleep
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.pipeline import run_daily_digest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("news-scraper-worker")


def execute_daily_run() -> None:
    session = SessionLocal()
    try:
        run_id = run_daily_digest(session)
        logger.info("completed daily digest run_id=%s", run_id)
    except Exception:
        logger.exception("daily digest failed")
    finally:
        session.close()


def main() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    if settings.run_on_startup:
        execute_daily_run()

    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.scheduler_timezone))
    scheduler.add_job(
        execute_daily_run,
        trigger=CronTrigger(
            hour=settings.daily_run_hour,
            minute=settings.daily_run_minute,
            timezone=ZoneInfo(settings.scheduler_timezone),
        ),
        id="daily-digest",
        replace_existing=True,
    )

    logger.info(
        "scheduler started timezone=%s hour=%s minute=%s",
        settings.scheduler_timezone,
        settings.daily_run_hour,
        settings.daily_run_minute,
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("scheduler stopped")
        sleep(0.1)


if __name__ == "__main__":
    main()
