from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from agent.config import AppConfig
from agent.pipeline import run_agent


def run_interval(query: str, minutes: int, config: AppConfig | None = None) -> None:
    config = config or AppConfig()
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_agent,
        trigger=IntervalTrigger(minutes=minutes),
        args=[query, config],
        max_instances=1,
        coalesce=True,
    )

    print(f"Starting scheduler for query '{query}' every {minutes} minute(s).")
    print("Press Ctrl+C to stop.")
    run_agent(query, config)
    scheduler.start()
