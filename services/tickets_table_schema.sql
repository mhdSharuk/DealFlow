-- schema.sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignee_name VARCHAR NOT NULL,
    task_description TEXT NOT NULL,
    blocker_notes TEXT,
    status VARCHAR DEFAULT 'To Do',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    meeting_id VARCHAR
);
