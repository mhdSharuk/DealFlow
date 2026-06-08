import os
from dotenv import load_dotenv
from celery import Celery

load_dotenv(dotenv_path=os.getcwd() + '/.env', override=True)

app = Celery("dealflow")

redis_url = os.getenv("REDIS_URL")

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
