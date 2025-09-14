from celery import Celery
from app.core.config import settings

# This is the central Celery application instance
celery_app = Celery(
    "code_review_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    # We explicitly tell Celery where to find our tasks module.
    # This is more robust than autodiscovery.
    include=['app.services.tasks']
)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
)
