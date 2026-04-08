"""
Developlus API — Celery Client (API → Worker köprüsü)
FastAPI'den Celery task göndermek için kullanılır.
"""
from celery import Celery
import os

_celery_app = Celery(
    "developlus",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
)


@_celery_app.task(name="src.tasks.document_tasks.index_document")
def index_document_task(document_id: str, text: str = None, pdf_hex: str = None):
    """Stub — gerçek implementasyon worker servisinde."""
    pass
