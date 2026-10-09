"""Upgrade diagnosis: what changes between the version you run and another, as a background
job."""

from fastapi import APIRouter, HTTPException, status

from dep_watch_agent.api.deps import JobsDep, SessionsDep, SystemsDep, pick_system
from dep_watch_agent.api.routes.issues import dropped_out, evidence_out, sorted_versions
from dep_watch_agent.api.schemas import JobOut, UpgradeItemOut, UpgradeRequest, UpgradeResponse
from dep_watch_agent.check import NotAnswerable, answerable

router = APIRouter(tags=["upgrade"])


@router.post(
    "/upgrade",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        200: {
            "model": UpgradeResponse,
            "description": "Not returned here: the ``result`` of the job once it succeeds",
        },
        409: {},
        422: {},
        503: {},
    },
)
def start_upgrade(body: UpgradeRequest, jobs: JobsDep, sessions: SessionsDep, systems: SystemsDep):
    """Compare each candidate issue's answer at ``from_version`` and ``to_version``: fixed by
    the move, new risks, unverified at the target, still affected, inconclusive. Poll
    ``/jobs/{id}``; ``progress`` counts issues read, and ``result`` is an ``UpgradeResponse``.
    422 when either version isn't a release of the project's dependency, or both are the same;
    503 when ``read`` asks for model calls and no system is registered."""
    from dep_watch_agent.upgrade import diagnose

    try:
        dependency = answerable(body.project, body.from_version)
        answerable(body.project, body.to_version)
    except NotAnswerable as exc:
        raise HTTPException(422, str(exc)) from None
    scheme = dependency.scheme
    if scheme.parse(body.from_version) == scheme.parse(body.to_version):
        raise HTTPException(422, "The two versions are the same")
    name = pick_system(systems, body.system) if systems or body.read else None

    def run(progress):
        with sessions() as session:
            result = diagnose(
                session,
                dependency,
                body.from_version,
                body.to_version,
                name,
                systems[name](dependency) if name else None,
                read=body.read,
                on_issue=progress,
            )
        response = UpgradeResponse(
            project=dependency.project,
            from_version=result.from_version,
            to_version=result.to_version,
            direction=result.direction,
            system=result.system,
            candidates=result.candidates,
            releases_between=result.releases_between,
            counts=result.counts,
            unchecked=result.unchecked,
            read=result.read,
            errors=result.errors,
            items=[
                UpgradeItemOut(
                    issue_key=item.issue_key,
                    url=item.url,
                    summary=item.summary,
                    status=item.status,
                    resolution=item.resolution,
                    updated_at=item.updated_at,
                    fix_versions=sorted_versions(item.fix_versions, scheme),
                    current=item.current,
                    target=item.target,
                    change=item.change,
                    decided_by=item.decided_by,
                    cached=item.cached,
                    evidence=evidence_out(item.evidence),
                    dropped=dropped_out(item.dropped),
                    error=item.error,
                )
                for item in result.items
            ],
        )
        return response.model_dump(mode="json")

    params = {**body.model_dump(mode="json"), "system": name}
    return jobs.submit("upgrade", run, key=f"upgrade:{name}", params=params)
