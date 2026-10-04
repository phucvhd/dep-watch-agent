"""Request and response bodies. These are the contract with the frontend (see ``/openapi.json``)."""

from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# JQL is built from the project key, so only plain keys are accepted.
ProjectKey = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$", max_length=32)]
# Dataset and run names become directory and file names.
FILE_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
FileName = Annotated[str, StringConstraints(pattern=FILE_NAME_PATTERN, max_length=128)]
IssueKey = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*-\d+$", max_length=64)]

Answer = Literal["affected", "not_affected", "insufficient_information"]
EvidenceKind = Literal["introduced", "affects", "unaffected", "fix"]


class DependencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    project: str = Field(description="Pass as `project` to /versions, /issues, /scan, /sync/jira")
    tracker_url: str


# --- repository scan -----------------------------------------------------------------------


class RepoFile(BaseModel):
    path: str = Field(max_length=512, description="Path in the repository; a label only")
    content: str = Field(max_length=2_000_000)


class RepoScanRequest(BaseModel):
    files: list[RepoFile] = Field(max_length=500, description="Manifest files and their text")


class DetectedDependencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    name: str
    version: str | None = Field(description="None when the manifests don't resolve it")
    family: str | None = Field(description="A known family id, e.g. kafka or spark")
    ecosystem: Literal["maven", "pypi", "npm", "image"]
    watchable: bool = Field(description="Supported and at a known release: can be watched")
    reason: str | None = Field(description="Why it can't be watched")
    artifacts: list[str]
    files: list[str]
    notes: list[str] = Field(description="How a version was read, e.g. from a Confluent image")


class RepoScanResponse(BaseModel):
    files_read: list[str]
    dependencies: list[DetectedDependencyOut]


class Health(BaseModel):
    status: Literal["ok"]
    version: str
    db_revision: str | None


# --- issues and versions -----------------------------------------------------------------


class IssueSummary(BaseModel):
    key: str
    url: str
    summary: str
    issue_type: str | None
    status: str | None
    resolution: str | None
    priority: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class IssuePage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[IssueSummary]


class Comment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author: str | None
    body: str
    created_at: datetime


class IssueDetail(IssueSummary):
    project: str
    description: str | None
    labels: list[str]
    components: list[str]
    affects_versions: list[str]
    fix_versions: list[str]
    comments: list[Comment]


class KafkaVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    released: bool
    archived: bool
    release_date: date | None


# --- check -------------------------------------------------------------------------------


class CheckRequest(BaseModel):
    issue_key: IssueKey
    kafka_version: str = Field(examples=["3.6.1"])
    system: str | None = Field(None, description="Default: the first registered system")


class EvidenceOut(BaseModel):
    version: str
    kind: EvidenceKind
    quote: str


class DroppedEvidenceOut(EvidenceOut):
    reason: str


class CheckResponse(BaseModel):
    issue_key: str
    url: str
    summary: str
    kafka_version: str
    answer: Answer
    system: str
    decided_by: str = Field(
        description="fix_versions when JIRA's fix versions settle it (the system isn't called); "
        "otherwise the system"
    )
    cached: bool = Field(description="The system's facts were stored from an earlier run")
    fix_versions: list[str] = Field(description="Given as structured input, from JIRA")
    evidence: list[EvidenceOut] = Field(description="Cited facts the decision used")
    dropped: list[DroppedEvidenceOut] = Field(description="Facts rejected, with the reason")


class StoredAnswer(BaseModel):
    answered: bool = Field(description="False when only a model call (POST /check) can answer")
    system: str | None
    result: CheckResponse | None = None


class IssueStats(BaseModel):
    total: int
    bugs: int
    open_bugs: int
    fixed_bugs: int
    read: int = Field(description="Issues whose text a model has read (facts stored)")
    newest: datetime | None = Field(description="The most recent update among synced issues")


# --- scan --------------------------------------------------------------------------------


class ScanRequest(BaseModel):
    kafka_version: str = Field(examples=["3.9.1"])
    project: ProjectKey = "KAFKA"
    since: datetime | None = Field(
        None, description="Only issues updated since then, e.g. the last scan (alerting)"
    )
    limit: int = Field(
        50,
        ge=1,
        le=10_000,
        description="At most this many issues, newest first. Each one the "
        "fix versions don't settle costs a model call.",
    )
    system: str | None = Field(None, description="Default: the first registered system")


class ScanItemOut(BaseModel):
    issue_key: str
    url: str
    summary: str
    status: str | None
    resolution: str | None
    updated_at: datetime
    answer: Answer
    decided_by: str
    cached: bool
    fix_versions: list[str]
    evidence: list[EvidenceOut]
    dropped: list[DroppedEvidenceOut]
    error: str | None = Field(description="Why the issue couldn't be answered, if it failed")


class ScanResponse(BaseModel):
    """The ``result`` of a finished scan job. Items: affected first, then
    insufficient_information, then not_affected; newest first within each."""

    kafka_version: str
    system: str
    since: datetime | None
    candidates_total: int = Field(description="Issues matching the filters, before the limit")
    scanned: int
    counts: dict[str, int]
    errors: int
    cached: int = Field(description="Issues answered from stored facts, without a model call")
    items: list[ScanItemOut]


# --- jobs --------------------------------------------------------------------------------


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    key: str | None
    params: dict[str, Any]
    status: Literal["queued", "running", "succeeded", "failed"]
    progress: int
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


# --- sync --------------------------------------------------------------------------------


class SyncRequest(BaseModel):
    project: ProjectKey = "KAFKA"
    full: bool = Field(False, description="Ignore the watermark and re-sync every issue")
    request_delay: float = Field(1.0, ge=0.5, le=60, description="Seconds between JIRA requests")


class SyncState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    watermark: datetime
    updated_at: datetime


# --- eval --------------------------------------------------------------------------------


class DatasetSummary(BaseModel):
    name: str
    design: str
    labeled: int
    total: int


class SampleRequest(BaseModel):
    name: FileName
    size: int = Field(100, ge=1, le=1000)
    seed: int = 20260927
    design: Literal["v1", "v2"] = "v2"
    force: bool = Field(False, description="Overwrite an existing dataset (loses its labels)")


class SampleResponse(BaseModel):
    name: str
    issues: int
    cases: int
    strata_counts: dict[str, Any]
    case_basis_counts: dict[str, Any]


class DatasetStatus(BaseModel):
    name: str
    labeled: int
    total: int
    problems: list[str] = Field(description="Problems other than unlabeled cases")
    ready: bool = Field(description="Fully labeled with no problems; can be uploaded")


class UploadResponse(BaseModel):
    name: str
    uploaded: int


class EvalRunRequest(BaseModel):
    dataset: FileName = "kafka-ground-truth-v2"
    system: str = Field(description="A registered system; runs are compared with each other")
    run_name: FileName | None = Field(None, description="Default: <system>-<UTC timestamp>")
    provisional: bool = Field(
        False, description="Score against JIRA metadata answers; allowed before labeling is done"
    )
    langfuse: bool = Field(False, description="Run as a Langfuse experiment on the dataset")


class EvalRunSummary(BaseModel):
    run_name: str
    system: str
    dataset: str
    provisional: bool
    metrics: dict[str, Any]


class EvalRun(EvalRunSummary):
    results: list[dict[str, Any]]
