import threading

import pytest

from dep_watch_agent.api.jobs import JobConflict, JobRegistry


def blocking(release: threading.Event):
    def fn(progress):
        release.wait(10)
        return {}

    return fn


def test_same_key_conflicts_while_active():
    jobs, release = JobRegistry(), threading.Event()
    first = jobs.submit("sync", blocking(release), key="sync:KAFKA")

    with pytest.raises(JobConflict) as exc:
        jobs.submit("sync", blocking(release), key="sync:KAFKA")
    assert exc.value.existing is first
    assert len(jobs.list()) == 1  # the rejected job leaves no trace

    release.set()
    jobs.wait(first.id, timeout=10)
    second = jobs.submit("sync", blocking(release), key="sync:KAFKA")  # finished jobs don't block
    assert jobs.wait(second.id, timeout=10).status == "succeeded"


def test_different_keys_run_together():
    jobs, release = JobRegistry(), threading.Event()
    jobs.submit("sync", blocking(release), key="sync:KAFKA")
    jobs.submit("sync", blocking(release), key="sync:ZOOKEEPER")
    release.set()


def test_jobs_without_a_key_never_conflict():
    jobs, release = JobRegistry(), threading.Event()
    a = jobs.submit("eval-run", blocking(release))
    b = jobs.submit("eval-run", blocking(release))
    release.set()
    assert jobs.wait(a.id, timeout=10).status == "succeeded"
    assert jobs.wait(b.id, timeout=10).status == "succeeded"
