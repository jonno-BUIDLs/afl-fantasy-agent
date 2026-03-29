"""APScheduler jobs for automated round briefings."""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


def run_pre_round():
    from afl_fantasy.orchestrator import run_pre_round_brief
    logger.info("Scheduler: running pre-round brief")
    try:
        run_pre_round_brief()
    except Exception as e:
        logger.error(f"Pre-round brief failed: {e}")
        raise


def run_data_sync():
    from afl_fantasy.orchestrator import sync_data
    logger.info("Scheduler: syncing data")
    try:
        sync_data()
    except Exception as e:
        logger.error(f"Data sync failed: {e}")


def start():
    scheduler = BlockingScheduler(timezone="Australia/Melbourne")

    # Full strategy brief: Wednesday nights (pre-lockout research time)
    scheduler.add_job(
        run_pre_round,
        CronTrigger(day_of_week="wed", hour=20, minute=0),
        id="pre_round_brief",
        name="Pre-round strategy brief",
    )

    # Data sync: twice daily (keep prices/scores current)
    scheduler.add_job(
        run_data_sync,
        CronTrigger(hour="8,20", minute=0),
        id="data_sync",
        name="Twice-daily data sync",
    )

    logger.info("Scheduler started. Jobs: pre_round_brief (Wed 8pm), data_sync (8am/8pm)")
    scheduler.start()
