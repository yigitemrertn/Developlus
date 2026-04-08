"""Developlus Worker — Celery Application"""
import os
from celery import Celery
from celery.schedules import crontab

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

app = Celery(
    "developlus",
    broker=broker_url,
    backend=result_backend,
    include=[
        "src.tasks.document_tasks",
        "src.tasks.cleanup_tasks",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_routes={
        "src.tasks.document_tasks.*": {"queue": "documents"},
        "src.tasks.cleanup_tasks.*": {"queue": "default"},
    },
)

# Zamanlanmış görevler
app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "src.tasks.cleanup_tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=3, minute=0),  # Her gece 03:00
    },
    "cleanup-failed-documents": {
        "task": "src.tasks.cleanup_tasks.cleanup_failed_documents",
        "schedule": crontab(hour=4, minute=0),  # Her gece 04:00
    },
}
