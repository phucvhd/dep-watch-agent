"""Read a repository's dependencies from its manifest files (the browser sends their text)."""

from fastapi import APIRouter

from dep_watch_agent.api.schemas import RepoScanRequest, RepoScanResponse
from dep_watch_agent.manifests import ManifestFile, detect, is_manifest

router = APIRouter(tags=["repo"])


@router.post("/repo/scan", response_model=RepoScanResponse)
def scan_repo(body: RepoScanRequest) -> RepoScanResponse:
    """Every dependency the manifests declare, grouped by family and version. Files that aren't
    manifests are ignored; paths are labels and are never opened on the server."""
    files = [ManifestFile(f.path, f.content) for f in body.files if is_manifest(f.path)]
    return RepoScanResponse(
        files_read=[f.path for f in files],
        dependencies=detect(files),  # type: ignore[arg-type]
    )
