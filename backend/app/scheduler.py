import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/New_York")


def register_jobs() -> None:
    pass


def start() -> None:
    register_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d job(s)", len(scheduler.get_jobs()))


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
