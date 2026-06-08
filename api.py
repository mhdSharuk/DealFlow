import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import DATABASE_PATH, INPUT_DIR, PROCESSING_DIR, ensure_directories
from services.job_service import JobService
from worker.tasks import process_transcript

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("dealflow.api")

job_service: Optional[JobService] = None


def _reset_stuck_jobs() -> None:
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("UPDATE jobs SET status='failed', error_message='Server restart' WHERE status='processing'")
        conn.commit()
        conn.close()
    except Exception as exc:
        log.warning("Could not reset stuck jobs: %s", exc)


async def file_watcher_loop() -> None:
    seen: set = set()
    while True:
        try:
            for json_file in sorted(INPUT_DIR.glob("*.json")):
                if json_file.name in seen:
                    continue
                if job_service.job_exists_for_file(json_file.name):
                    seen.add(json_file.name)
                    continue
                seen.add(json_file.name)
                try:
                    raw = json.loads(json_file.read_text(encoding="utf-8"))
                    job_id = job_service.create_job(raw, source_file=json_file.name)
                    dest = PROCESSING_DIR / f"{job_id}.json"
                    json_file.rename(dest)
                    process_transcript.apply_async(args=[job_id], queue="transcripts")
                    log.info("Dispatched  job=%s  file=%s", job_id[:8], json_file.name)
                except Exception as exc:
                    log.error("Failed to ingest %s: %s", json_file.name, exc)
        except Exception as exc:
            log.error("file_watcher_loop error: %s", exc)
        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global job_service

    ensure_directories()
    job_service = JobService()
    _reset_stuck_jobs()

    log.info("Starting file watcher — dispatching jobs to Celery via Redis")
    watcher_task = asyncio.create_task(file_watcher_loop())

    yield

    watcher_task.cancel()
    await asyncio.gather(watcher_task, return_exceptions=True)
    log.info("Shutdown complete")


app = FastAPI(title="DealFlow API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "broker": "redis", "queue": "transcripts"}


@app.get("/jobs")
async def list_jobs() -> List[Dict[str, Any]]:
    return job_service.get_all_jobs()


@app.get("/jobs/dead")
async def list_dead_jobs() -> List[Dict[str, Any]]:
    return job_service.get_jobs_by_status("dead")


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
