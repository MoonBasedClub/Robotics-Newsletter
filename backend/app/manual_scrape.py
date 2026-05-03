import argparse
import logging

from app.database import Base, SessionLocal, engine
from app.pipeline import run_daily_digest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("news-scraper-manual")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manually start a fresh news scrape run."
    )
    parser.add_argument(
        "--date",
        help="Optional local schedule date to run, for example 2026-05-03.",
    )
    args = parser.parse_args(argv)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        run_id = run_daily_digest(session, date_override=args.date, force=True)
        logger.info("manual scrape completed run_id=%s", run_id)
        print(f"Manual scrape completed. run_id={run_id}")
        return 0
    except Exception:
        logger.exception("manual scrape failed")
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
