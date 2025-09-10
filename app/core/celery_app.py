"""
Celery application setup and configuration.
"""
from celery import Celery
from ..core.config import settings

# Initialize the Celery application
celery_app = Celery(
    "code_review_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["services.tasks"]  # List of modules to import when the worker starts
)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,  # Expire results after 1 hour
)

if __name__ == '__main__':
    celery_app.start()
