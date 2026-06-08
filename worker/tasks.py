import asyncio
import traceback

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


@app.task(
    bind=True,
    max_retries=3,
    queue="transcripts",
    name="worker.tasks.process_transcript",
)
def process_transcript(self, job_id: str) -> None:
    job = _job_service.get_job(job_id)
    if not job:
        log.warning("job=%s not found in DB — skipping", job_id[:8])
        return

    _job_service.update_job_status(job_id, "processing")
    source = PROCESSING_DIR / f"{job_id}.json"
    log.info("Processing job=%s  file=%s", job_id[:8], job.get("source_file"))

    try:
        result = asyncio.run(_orchestrator.process_transcript(job["raw_payload"]))

        meeting_id = (result.get("metadata") or {}).get("meeting_id")
        _job_service.update_job_status(job_id, "complete", result=result, meeting_id=meeting_id)
        if source.exists():
            source.rename(PROCESSED_DIR / f"{job_id}.json")

        log.info("Completed job=%s  meeting_id=%s", job_id[:8], meeting_id)

    except Exception as exc:
        root = exc.exceptions[0] if isinstance(exc, ExceptionGroup) and exc.exceptions else exc

        err = f"{type(root).__name__}: {root}\n\nFull traceback:\n{traceback.format_exc()}"
        retry_num = self.request.retries + 1

        if retry_num <= self.max_retries:
            _job_service.update_job_status(job_id, "failed", error_message=err)
            countdown = (2 ** self.request.retries) * 10  # 30s, 60s, 120s
            log.warning("Retrying job=%s  attempt=%d/%d  in=%ds", job_id[:8], retry_num, self.max_retries, countdown)
            raise self.retry(exc=root, countdown=countdown)

        if source.exists():
            source.rename(PROCESSED_DIR / f"{job_id}_failed.json")
        handle_dead_letter.apply_async(args=[job_id, str(root)], queue="dead_letter")
        raise
