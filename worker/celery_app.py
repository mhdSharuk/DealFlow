import os

from celery import Celery

app = Celery("dealflow")

app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    # Acknowledge the message only after the task finishes — guarantees at-least-once delivery.
    # If the worker dies mid-task the broker re-queues the message for another worker.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "worker.tasks.process_transcript": {"queue": "transcripts"},
        "worker.tasks.handle_dead_letter": {"queue": "dead_letter"},
    },
)
