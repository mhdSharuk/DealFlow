import asyncio
import logging
import traceback

from celery import Task
from celery.utils.log import get_task_logger

from core.config import PROCESSED_DIR, PROCESSING_DIR
from core.orchestrator import DealFlowOrchestrator
from services.job_service import JobService
from worker.celery_app import app

log = get_task_logger(__name__)

_job_service = JobService()
_orchestrator = DealFlowOrchestrator()


@app.task(queue="dead_letter")
def handle_dead_letter(job_id: str, error: str) -> None:
    log.error("DLQ received job=%s  error=%s", job_id[:8], error[:200])
    _job_service.update_job_status(job_id, "dead", error_message=f"[DLQ] {error}")


class _TranscriptTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = args[0] if args else "unknown"
        if self.request.retries >= self.max_retries:
            log.error("Max retries reached for job=%s — routing to dead_letter queue", job_id[:8])
            handle_dead_letter.apply_async(args=[job_id, str(exc)], queue="dead_letter")


@app.task(
    bind=True,
    base=_TranscriptTask,
    max_retries=3,
    queue="transcripts",
    name="worker.tasks.process_transcript",
)
def process_transcript(self, job_id: str) -> None:
    job = _job_service.get_job(job_id)
    if job is None:
        log.warning("job=%s not found in DB — skipping", job_id[:8])
        return

    _job_service.update_job_status(job_id, "processing")
    source = PROCESSING_DIR / f"{job_id}.json"
    log.info("Processing job=%s  file=%s", job_id[:8], job.get("source_file"))

    try:
        result = asyncio.run(_orchestrator.process_transcript(job["raw_payload"]))

        meeting_id = (result.get("metadata") or {}).get("meeting_id")
        if result.get("agent_2_tickets"):
            _orchestrator.save_tasks_to_database(result["agent_2_tickets"], meeting_id)

        _job_service.update_job_status(job_id, "complete", result=result, meeting_id=meeting_id)
        if source.exists():
            source.rename(PROCESSED_DIR / f"{job_id}.json")

        log.info("Completed job=%s  meeting_id=%s", job_id[:8], meeting_id)

    except Exception as exc:
        # Unwrap ExceptionGroup from ADK's ParallelAgent
        root = exc
        if isinstance(exc, ExceptionGroup) and exc.exceptions:
            root = exc.exceptions[0]

        err = f"{type(root).__name__}: {root}\n\nFull traceback:\n{traceback.format_exc()}"
        retry_num = self.request.retries + 1

        if retry_num <= self.max_retries:
            _job_service.update_job_status(job_id, "failed", error_message=err)
            countdown = (2 ** self.request.retries) * 30  # 30s, 60s, 120s
            log.warning("Retrying job=%s  attempt=%d/%d  in=%ds", job_id[:8], retry_num, self.max_retries, countdown)
            raise self.retry(exc=root, countdown=countdown)

        if source.exists():
            source.rename(PROCESSED_DIR / f"{job_id}_failed.json")
        raise
