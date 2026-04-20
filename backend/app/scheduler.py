import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/New_York")


def register_jobs() -> None:
    from app.jobs.quotes import refresh_quotes_job

    scheduler.add_job(
        refresh_quotes_job,
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5"),
        id="refresh_quotes_market_hours",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_quotes_job,
        CronTrigger(hour="*", minute=0),
        id="refresh_quotes_off_hours",
        replace_existing=True,
    )


def start() -> None:
    register_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d job(s)", len(scheduler.get_jobs()))


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
