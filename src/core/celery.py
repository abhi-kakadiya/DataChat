from celery import Celery
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

celery_app = Celery(
    "datalens",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_processing",
        "app.tasks.analytics",
        "app.tasks.insights"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    beat_schedule={
        "cleanup-old-files": {
            "task": "app.tasks.data_processing.cleanup_old_files",
            "schedule": 86400.0,
        },
        "generate-dataset-insights": {
            "task": "app.tasks.insights.generate_background_insights",
            "schedule": 3600.0,
        },
        "update-dspy-models": {
            "task": "app.tasks.analytics.update_dspy_models",
            "schedule": 21600.0,
        },
    },
)

if not settings.DEBUG:
    celery_app.conf.update(
        worker_hijack_root_logger=False,
        worker_log_color=False,
    )


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"

