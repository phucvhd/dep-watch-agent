"""In-process background jobs for work that outlives a request (JIRA sync, eval runs).

Each job runs on its own daemon thread and its state lives in memory: a restart forgets
finished jobs and abandons running ones (daemon threads don't hold up shutdown). That is safe
for both job kinds: a JIRA sync only saves its watermark after it completes, so an abandoned
sync is simply redone next time, and an eval run writes its results file at the end.

A job may carry a ``key`` naming the resource it works on (``sync:KAFKA``). Two jobs with the
same key must not run at the same time.
"""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

JobStatus = Literal["queued", "running", "succeeded", "failed"]

# The job function gets a callback to report progress (e.g. issues synced so far) and returns
# a JSON-serializable result.
JobFn = Callable[[Callable[[int], None]], dict[str, Any]]


class JobConflict(Exception):
    def __init__(self, existing: "Job"):
        super().__init__(f"job {existing.id} is already {existing.status} for {existing.key}")
        self.existing = existing


@dataclass
class Job:
    id: str
    kind: str
    key: str | None
    params: dict[str, Any]
    status: JobStatus = "queued"
    progress: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.status in ("queued", "running")


class JobRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}
        self._done: dict[str, threading.Event] = {}

    def submit(
        self, kind: str, fn: JobFn, *, key: str | None = None, params: dict[str, Any] | None = None
    ) -> Job:
        """Start ``fn`` in the background. Returns the job to poll."""
        with self._lock:
            if key is not None and (active_job := self.active(key)) is not None:
                raise JobConflict(active_job)
            job = Job(id=uuid.uuid4().hex, kind=kind, key=key, params=params or {})
            self._jobs[job.id] = job
            self._done[job.id] = threading.Event()
        threading.Thread(target=self._run, args=(job, fn), name=f"job-{kind}", daemon=True).start()
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list(self, kind: str | None = None) -> list[Job]:
        jobs = [j for j in self._jobs.values() if kind is None or j.kind == kind]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def active(self, key: str) -> Job | None:
        return next((j for j in self._jobs.values() if j.key == key and j.active), None)

    def wait(self, job_id: str, timeout: float | None = None) -> Job:
        """Block until the job finishes. For tests."""
        if not self._done[job_id].wait(timeout):
            raise TimeoutError(f"job {job_id} still {self._jobs[job_id].status}")
        return self._jobs[job_id]

    def _run(self, job: Job, fn: JobFn) -> None:
        job.status = "running"
        job.started_at = datetime.now(UTC)

        def progress(count: int) -> None:
            job.progress = count

        try:
            job.result = fn(progress)
            job.status = "succeeded"
        except Exception as exc:  # a failed job is reported through its status, not raised
            job.error = f"{type(exc).__name__}: {exc}"
            job.status = "failed"
        finally:
            job.finished_at = datetime.now(UTC)
            self._done[job.id].set()
