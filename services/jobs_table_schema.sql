CREATE TABLE IF NOT EXISTS jobs (
    id            TEXT PRIMARY KEY,
    meeting_id    TEXT,
    source_file   TEXT,
    status        TEXT NOT NULL DEFAULT 'pending'
                      CHECK(status IN ('pending','processing','complete','failed','dead')),
    raw_payload   TEXT NOT NULL,
    result        TEXT,
    error_message TEXT,
    created_at    TEXT NOT NULL,
    started_at    TEXT,
    completed_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
