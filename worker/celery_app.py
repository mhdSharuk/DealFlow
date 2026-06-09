import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.getcwd() + '/.env', override=True)

app = Celery("dealflow", include=["worker.tasks"])

redis_url = os.getenv("REDIS_URL")

app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
    broker_use_ssl=None,
    redis_backend_use_ssl=None,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "worker.tasks.process_transcript": {"queue": "transcripts"},
        "worker.tasks.handle_dead_letter": {"queue": "dead_letter"},
    },
)
