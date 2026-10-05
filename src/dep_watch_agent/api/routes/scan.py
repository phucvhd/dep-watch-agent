"""Scan synced issues for one pinned version: the alerting flow, as a background job."""

from fastapi import APIRouter, HTTPException, status

from dep_watch_agent.api.deps import JobsDep, SessionsDep, SystemsDep, pick_system
from dep_watch_agent.api.routes.issues import dropped_out, evidence_out, sorted_versions
from dep_watch_agent.api.schemas import JobOut, ScanItemOut, ScanRequest, ScanResponse
from dep_watch_agent.check import NotAnswerable, answerable

router = APIRouter(tags=["scan"])


@router.post(
    "/scan",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        200: {
            "model": ScanResponse,
            "description": "Not returned here: the ``result`` of the job once it succeeds",
        },
        409: {},
        422: {},
        503: {},
    },
)
def start_scan(body: ScanRequest, jobs: JobsDep, sessions: SessionsDep, systems: SystemsDep):
    """Answer each candidate issue of ``project`` for ``version``: affected, not_affected or
    insufficient_information, with cited facts and a link. Poll ``/jobs/{id}``; ``progress``
    counts issues answered, and ``result`` is a ``ScanResponse``. One scan per system at a
    time, since they share the model server. 422 when the project's dependency isn't answered
    or the version isn't one of its releases."""
    from dep_watch_agent.scan import scan_version

    try:
        dependency = answerable(body.project, body.version)
    except NotAnswerable as exc:
        raise HTTPException(422, str(exc)) from None
    name = pick_system(systems, body.system)

    def run(progress):
        with sessions() as session:
            result = scan_version(
                session,
                dependency,
                body.version,
                name,
                systems[name](),
                since=body.since,
                limit=body.limit,
                on_issue=progress,
            )
        response = ScanResponse(
            version=result.version,
            system=result.system,
            since=result.since,
            candidates_total=result.candidates_total,
            scanned=len(result.items),
            counts=result.counts,
            errors=result.errors,
            cached=result.cached,
            items=[
                ScanItemOut(
                    issue_key=item.issue_key,
                    url=item.url,
                    summary=item.summary,
                    status=item.status,
                    resolution=item.resolution,
                    updated_at=item.updated_at,
                    answer=item.answer,
                    decided_by=item.decided_by,
                    cached=item.cached,
                    fix_versions=sorted_versions(item.fix_versions, dependency.scheme),
                    evidence=evidence_out(item.evidence),
                    dropped=dropped_out(item.dropped),
                    error=item.error,
                )
                for item in result.items
            ],
        )
        return response.model_dump(mode="json")

    params = {**body.model_dump(mode="json"), "system": name}
    return jobs.submit("scan", run, key=f"scan:{name}", params=params)
