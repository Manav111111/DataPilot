import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "data_intelligence_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.collection.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max hard limit
    task_soft_time_limit=3000,
    worker_concurrency=settings.COLLECTION_CONCURRENCY,
    worker_prefetch_multiplier=1,
    broker_connection_timeout=0.5,
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
)

