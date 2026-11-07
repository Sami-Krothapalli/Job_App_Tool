from datetime import date, datetime

import pytest

from job_app_tool.db import (
    attempts_on,
    connect,
    get_job,
    mark_synced,
    queued_jobs,
    record_finished_run,
    recover_interrupted,
    run_finished_on,
    save_new_jobs,
    seed,
    set_status,
    start_submitting,
    unsynced,
)


def job(**changes):
    """A job shaped like one entry in listings.json."""
    base = {
        "id": "abc-123",
        "company_name": "Acme",
        "title": "Software Engineer, New Grad",
        "url": "https://jobs.lever.co/acme/abc-123",
        "category": "Software",
        "locations": ["Austin, TX"],
        "sponsorship": "Other",
        "active": True,
        "is_visible": True,
        "date_posted": 1793000000,
    }
    return base | changes


def ids(rows):
    return [row["id"] for row in rows]


@pytest.fixture
def conn(tmp_path):
    """A fresh database file per test, deleted afterwards by pytest."""
    connection = connect(tmp_path / "jobs.db")
    yield connection
    connection.close()


# save_new_jobs(conn, jobs) stores jobs it has never seen and returns only those.


def test_a_job_is_new_only_the_first_time(conn):
    assert ids(save_new_jobs(conn, [job()])) == ["abc-123"]
    assert save_new_jobs(conn, [job()]) == []


def test_a_saved_job_starts_as_new(conn):
    save_new_jobs(conn, [job()])

    assert get_job(conn, "abc-123")["status"] == "new"


def test_saved_jobs_are_remembered_after_reconnecting(tmp_path):
    first = connect(tmp_path / "jobs.db")
    save_new_jobs(first, [job()])
    first.close()

    second = connect(tmp_path / "jobs.db")
    assert save_new_jobs(second, [job()]) == []
    second.close()


def test_inactive_jobs_are_not_stored_so_a_reactivated_job_is_still_new(conn):
    assert save_new_jobs(conn, [job(active=False)]) == []
    assert get_job(conn, "abc-123") is None

    assert ids(save_new_jobs(conn, [job()])) == ["abc-123"]


def test_unknown_job_is_none(conn):
    assert get_job(conn, "nope") is None


# set_status(conn, job_id, status, reason=None) records what happened to a job.


def test_set_status_records_the_reason(conn):
    save_new_jobs(conn, [job()])
    set_status(conn, "abc-123", "skipped", "category: Hardware")

    row = get_job(conn, "abc-123")
    assert (row["status"], row["reason"]) == ("skipped", "category: Hardware")


# seed(conn, jobs) records every job already in the feed as skipped, once, before the first run.


def test_seeding_marks_jobs_skipped_and_later_jobs_are_new(conn):
    seed(conn, [job(id="a"), job(id="b")])

    assert get_job(conn, "a")["status"] == "skipped"
    assert ids(save_new_jobs(conn, [job(id="a"), job(id="b"), job(id="c")])) == ["c"]


def test_seeding_leaves_an_applied_job_unchanged(conn):
    save_new_jobs(conn, [job()])
    set_status(conn, "abc-123", "applied")

    seed(conn, [job()])

    assert get_job(conn, "abc-123")["status"] == "applied"


# queued_jobs(conn, limit) returns the oldest queued jobs without changing them.


def test_queue_returns_the_oldest_jobs_up_to_the_limit(conn):
    jobs = [job(id=f"j{n:02}", date_posted=1793000000 + n) for n in range(12)]
    save_new_jobs(conn, list(reversed(jobs)))
    for j in jobs:
        set_status(conn, j["id"], "queued")

    assert ids(queued_jobs(conn, limit=10)) == [f"j{n:02}" for n in range(10)]
    assert get_job(conn, "j10")["status"] == "queued"
    assert get_job(conn, "j11")["status"] == "queued"


# start_submitting(conn, job_id, now) is written just before the submit click.


def test_start_submitting_sets_the_status(conn):
    save_new_jobs(conn, [job()])
    start_submitting(conn, "abc-123", datetime(2026, 11, 4, 9, 0))

    assert get_job(conn, "abc-123")["status"] == "submitting"


def test_a_job_left_submitting_moves_to_manual_at_startup(conn):
    save_new_jobs(conn, [job()])
    start_submitting(conn, "abc-123", datetime(2026, 11, 4, 9, 0))

    recover_interrupted(conn)

    row = get_job(conn, "abc-123")
    assert row["status"] == "manual"
    assert "submission" in row["reason"]


def test_recovery_leaves_other_jobs_alone(conn):
    save_new_jobs(conn, [job()])
    set_status(conn, "abc-123", "applied")

    recover_interrupted(conn)

    assert get_job(conn, "abc-123")["status"] == "applied"


# attempts_on(conn, day) counts submissions started that day: the daily cap.


def test_only_attempts_started_that_day_count(conn):
    save_new_jobs(conn, [job(id="old"), job(id="today")])
    start_submitting(conn, "old", datetime(2026, 11, 3, 9, 0))
    start_submitting(conn, "today", datetime(2026, 11, 4, 9, 0))

    assert attempts_on(conn, date(2026, 11, 4)) == 1


def test_a_finished_attempt_still_counts(conn):
    save_new_jobs(conn, [job()])
    start_submitting(conn, "abc-123", datetime(2026, 11, 4, 9, 0))
    set_status(conn, "abc-123", "applied")

    assert attempts_on(conn, date(2026, 11, 4)) == 1


# unsynced(conn) lists applied and manual jobs not yet copied to Notion.


def test_applied_jobs_are_unsynced_until_marked(conn):
    save_new_jobs(conn, [job()])
    set_status(conn, "abc-123", "applied")
    assert ids(unsynced(conn)) == ["abc-123"]

    mark_synced(conn, "abc-123")

    assert unsynced(conn) == []


def test_skipped_jobs_are_never_sent_to_notion(conn):
    save_new_jobs(conn, [job()])
    set_status(conn, "abc-123", "skipped", "category: Hardware")

    assert unsynced(conn) == []


def test_a_status_change_after_syncing_needs_syncing_again(conn):
    save_new_jobs(conn, [job()])
    set_status(conn, "abc-123", "manual", "site: Workday")
    mark_synced(conn, "abc-123")

    set_status(conn, "abc-123", "applied")

    assert ids(unsynced(conn)) == ["abc-123"]


# record_finished_run / run_finished_on: only a finished run counts for the day.


def test_a_day_with_no_finished_run(conn):
    assert run_finished_on(conn, date(2026, 11, 4)) is False


def test_a_finished_run_is_remembered_for_that_day_only(conn):
    record_finished_run(conn, date(2026, 11, 4))

    assert run_finished_on(conn, date(2026, 11, 4)) is True
    assert run_finished_on(conn, date(2026, 11, 5)) is False
