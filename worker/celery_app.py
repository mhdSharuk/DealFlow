import os

from celery import Celery

app = Celery("dealflow")

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "worker.tasks.process_transcript": {"queue": "transcripts"},
        "worker.tasks.handle_dead_letter": {"queue": "dead_letter"},
    },
)
