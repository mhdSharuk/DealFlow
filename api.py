import asyncio
import json
import logging
import sqlite3
import traceback
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import (
    API_BASE_URL,
    DATABASE_PATH,
    INPUT_DIR,
    PROCESSED_DIR,
    PROCESSING_DIR,
    ensure_directories,
)
from core.orchestrator import DealFlowOrchestrator
from services.job_service import JobService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("dealflow.api")

# ── Singletons ────────────────────────────────────────────────────────────────
job_queue: asyncio.Queue = asyncio.Queue()
job_service: Optional[JobService] = None
orchestrator: Optional[DealFlowOrchestrator] = None


# ── Startup helpers ───────────────────────────────────────────────────────────
def _reset_stuck_jobs() -> None:
    """Mark any jobs left in 'processing' from a previous crash as failed."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute(
            "UPDATE jobs SET status='failed', error_message='Server restart' "
            "WHERE status='processing'"
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        log.warning("Could not reset stuck jobs: %s", exc)


# ── Background tasks ──────────────────────────────────────────────────────────
async def file_watcher_loop() -> None:
    """
    Poll data/input/ every 3 seconds for new .json files.
    On discovery: read payload → create SQLite job → move file to processing/ → enqueue.
    """
    seen: set = set()
    while True:
        try:
            for json_file in sorted(INPUT_DIR.glob("*.json")):
                if json_file.name in seen:
                    continue
                # Skip files that already have a job record (survives server restarts)
                if job_service.job_exists_for_file(json_file.name):
                    seen.add(json_file.name)
                    continue
                seen.add(json_file.name)
                try:
                    raw = json.loads(json_file.read_text(encoding="utf-8"))
                    job_id = job_service.create_job(raw, source_file=json_file.name)
                    dest = PROCESSING_DIR / f"{job_id}.json"
                    json_file.rename(dest)
                    await job_queue.put(job_id)
                    log.info("Queued  job=%s  file=%s", job_id[:8], json_file.name)
                except Exception as exc:
                    log.error("Failed to ingest %s: %s", json_file.name, exc)
        except Exception as exc:
            log.error("file_watcher_loop error: %s", exc)
        await asyncio.sleep(3)


async def worker_loop() -> None:
    """
    Consume job_ids from the asyncio.Queue one at a time.
    Run DealFlowOrchestrator and update SQLite with results.
    """
    while True:
        job_id: str = await job_queue.get()
        job = job_service.get_job(job_id)
        if job is None:
            job_queue.task_done()
            continue

        job_service.update_job_status(job_id, "processing")
        source = PROCESSING_DIR / f"{job_id}.json"
        log.info("Processing job=%s  file=%s", job_id[:8], job.get("source_file"))

        try:
            result = await orchestrator.process_transcript(job["raw_payload"])
            meeting_id = (result.get("metadata") or {}).get("meeting_id")

            if result.get("agent_2_tickets"):
                orchestrator.save_tasks_to_database(result["agent_2_tickets"], meeting_id)

            job_service.update_job_status(
                job_id, "complete", result=result, meeting_id=meeting_id
            )
            if source.exists():
                source.rename(PROCESSED_DIR / f"{job_id}.json")
            log.info("Completed job=%s  meeting_id=%s", job_id[:8], meeting_id)

        except Exception as exc:
            # Unwrap ExceptionGroup (raised by ADK's ParallelAgent / asyncio.TaskGroup)
            # to surface the actual root-cause exception instead of the wrapper
            root = exc
            if isinstance(exc, ExceptionGroup) and exc.exceptions:
                root = exc.exceptions[0]

            err = f"{type(root).__name__}: {root}\n\nFull traceback:\n{traceback.format_exc()}"
            job_service.update_job_status(job_id, "failed", error_message=err)
            if source.exists():
                source.rename(PROCESSED_DIR / f"{job_id}_failed.json")
            log.error("Failed    job=%s  root_cause=%s: %s", job_id[:8], type(root).__name__, root)

        finally:
            job_queue.task_done()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global job_service, orchestrator

    ensure_directories()
    job_service = JobService()
    _reset_stuck_jobs()

    log.info("Initialising DealFlowOrchestrator…")
    orchestrator = DealFlowOrchestrator()
    log.info("Orchestrator ready — starting watcher and worker")

    watcher_task = asyncio.create_task(file_watcher_loop())
    worker_task  = asyncio.create_task(worker_loop())

    yield

    watcher_task.cancel()
    worker_task.cancel()
    await asyncio.gather(watcher_task, worker_task, return_exceptions=True)
    log.info("Shutdown complete")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="DealFlow API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "queue_size": job_queue.qsize()}


@app.get("/jobs")
async def list_jobs() -> List[Dict[str, Any]]:
    return job_service.get_all_jobs()


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    job = job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
