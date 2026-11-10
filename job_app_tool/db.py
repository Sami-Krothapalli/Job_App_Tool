import sqlite3


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL CHECK (
                status IN (
                    'new', 
                    'skipped', 
                    'manual', 
                    'queued', 
                    'submitting', 
                    'applied'
                    )
                ),
            reason TEXT,
            date_posted INTEGER,
            company_name TEXT,
            title TEXT,
            url TEXT,
            substart TEXT,
            notion_sync INTEGER NOT NULL DEFAULT 0
            );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            day TEXT PRIMARY KEY
        );
        """
    )

    return conn


def get_job(conn, job_id):
    pass


def save_new_jobs(conn, job_id):
    """Receives the whole list of jobs from the feed not one id"""
    pass


def set_status(conn, job_id, status, reason=None):
    pass
