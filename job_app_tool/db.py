"""The tool's memory: every job it has seen and what happened to it, in one SQLite file."""

import sqlite3
from job_app_tool.feed import is_open


def connect(path):
    """Open the database at `path`, creating the file and tables if missing.

    Rows come back as `sqlite3.Row`, so columns can be read by name.
    """
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
    """Return the job with this id as a dict, or None if it was never saved."""
    row = conn.execute(
        """
            SELECT * FROM jobs
            WHERE id = ?
        """,
        (job_id,),
    ).fetchone()
    if row is None:
        return None
    else:
        return dict(row)


def save_new_jobs(conn, jobs):
    """Save open jobs from the feed that aren't stored yet, with status 'new'.

    Receives the whole list of jobs from the feed, not one id. Returns only the
    newly saved jobs. Closed jobs are not stored, so one that reopens later is
    still new.
    """
    new_jobs = []
    for job in jobs:
        if not is_open(job):
            continue
        if get_job(conn, job["id"]) is not None:
            continue
    conn.execute(
        """
        INSERT INTO jobs (id, company_name, title, url, date_posted, status)
        VALUES (?, ?, ?, ?, ?, 'new) 
    """,
        (job["id"], job["company_name"], job["title"], job["url"], job["date_posted"]),
    )
    new_jobs.append(job)
    conn.commit()
    return new_jobs


def set_status(conn, job_id, status, reason=None):
    """Record what happened to a job, with an optional reason.

    Every change marks the job as not yet copied to Notion.
    """
    pass


def seed(conn, jobs):
    """Before the first run, mark every job already in the feed 'skipped'.

    Jobs already in the database are left unchanged.
    """
    pass


def queued_jobs(conn, limit):
    """Return up to `limit` queued jobs, oldest `date_posted` first.

    Only reads: the jobs stay queued.
    """
    pass


def start_submitting(conn, job_id, now):
    """Mark a job 'submitting' and record `now`, just before clicking submit.

    The saved time is what `attempts_on` counts for the daily cap.
    """
    pass


def recover_interrupted(conn):
    """At startup, move any job left 'submitting' to 'manual'.

    A job still 'submitting' means the last run stopped mid-submission, so it
    may or may not have gone through. The reason says to check it by hand.
    """
    pass


def attempts_on(conn, day):
    """Count submissions started on `day`, whatever their outcome.

    A failed attempt may still have reached the employer, so it counts.
    """
    pass


def unsynced(conn):
    """Return 'applied' and 'manual' jobs not yet copied to Notion.

    Skipped jobs never go to Notion.
    """
    pass


def mark_synced(conn, job_id):
    """Record that this job's latest status has been copied to Notion."""
    pass


def record_finished_run(conn, day):
    """Remember that a run finished on `day`."""
    pass


def run_finished_on(conn, day):
    """Return True if a run finished on `day`, otherwise False."""
    pass
