import os
import ssl

from celery import Celery

app = Celery("dealflow", include=["worker.tasks"])

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

ssl_options = {"ssl_cert_reqs": ssl.CERT_NONE} if redis_url.startswith("rediss://") else {}

app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
    broker_use_ssl=ssl_options or None,
    redis_backend_use_ssl=ssl_options or None,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "worker.tasks.process_transcript": {"queue": "transcripts"},
        "worker.tasks.handle_dead_letter": {"queue": "dead_letter"},
    },
)
