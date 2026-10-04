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
    fix_versions: list[str] = Field(description="Given as structured input, from JIRA")
    evidence: list[EvidenceOut] = Field(description="Cited facts the decision used")
    dropped: list[DroppedEvidenceOut] = Field(description="Facts rejected, with the reason")


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
    system: Literal["baseline"] = "baseline"
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
