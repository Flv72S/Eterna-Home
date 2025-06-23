from celery import Celery
from app.core.config import settings
import os

# Configurazione Celery
celery_app = Celery(
    "eterna_home",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=[
        "app.workers.bim_worker",
        "app.workers.conversion_worker"
    ]
)

# Configurazione task
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minuti
    task_soft_time_limit=25 * 60,  # 25 minuti
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Configurazione per task BIM
celery_app.conf.task_routes = {
    "app.workers.bim_worker.*": {"queue": "bim_conversion"},
    "app.workers.conversion_worker.*": {"queue": "bim_conversion"},
}

# Configurazione per task con priorità
celery_app.conf.task_annotations = {
    "app.workers.bim_worker.convert_ifc_to_gltf": {"rate_limit": "10/m"},
    "app.workers.bim_worker.convert_rvt_to_ifc": {"rate_limit": "5/m"},
    "app.workers.conversion_worker.process_bim_model": {"rate_limit": "20/m"},
}

if __name__ == "__main__":
    celery_app.start() 