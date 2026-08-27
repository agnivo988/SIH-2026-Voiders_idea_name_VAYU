import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(lambda: logger.info("Scheduled collection tick; demo/live job wiring is ready"), "cron", hour=6, minute=0, id="daily-collection", replace_existing=True)
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
