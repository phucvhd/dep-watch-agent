"""Typed view of a raw JIRA issue as returned by the REST API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

_JIRA_TIMESTAMP = "%Y-%m-%dT%H:%M:%S.%f%z"


@dataclass(frozen=True)
class JiraComment:
    id: int
    author: str | None
    body: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class JiraIssue:
    id: int
    key: str
    project: str
    summary: str
    description: str | None
    issue_type: str | None
    status: str | None
    resolution: str | None
    priority: str | None
    labels: list[str]
    components: list[str]
    affects_versions: list[str]
    fix_versions: list[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    comments: list[JiraComment]
    raw: dict[str, Any]


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, _JIRA_TIMESTAMP)


def parse_issue(raw: dict[str, Any]) -> JiraIssue:
    fields = raw["fields"]
    key = raw["key"]
    return JiraIssue(
        id=int(raw["id"]),
        key=key,
        project=key.split("-", 1)[0],
        summary=fields["summary"],
        description=fields.get("description"),
        issue_type=_name(fields.get("issuetype")),
        status=_name(fields.get("status")),
        resolution=_name(fields.get("resolution")),
        priority=_name(fields.get("priority")),
        labels=list(fields.get("labels") or []),
        components=_names(fields.get("components")),
        affects_versions=_names(fields.get("versions")),
        fix_versions=_names(fields.get("fixVersions")),
        created_at=parse_timestamp(fields["created"]),
        updated_at=parse_timestamp(fields["updated"]),
        resolved_at=_optional_timestamp(fields.get("resolutiondate")),
        comments=[_parse_comment(c) for c in (fields.get("comment") or {}).get("comments", [])],
        raw=raw,
    )


def comments_truncated(raw: dict[str, Any]) -> bool:
    """True if the search response left out some of the issue's comments."""
    comment = raw["fields"].get("comment") or {}
    return comment.get("total", 0) > len(comment.get("comments", []))


def _parse_comment(raw: dict[str, Any]) -> JiraComment:
    author = raw.get("author") or {}
    return JiraComment(
        id=int(raw["id"]),
        author=author.get("displayName") or author.get("name"),
        body=raw.get("body") or "",
        created_at=parse_timestamp(raw["created"]),
        updated_at=parse_timestamp(raw["updated"]),
    )


def _name(value: dict[str, Any] | None) -> str | None:
    return value["name"] if value else None


def _names(values: list[dict[str, Any]] | None) -> list[str]:
    return sorted({v["name"] for v in values or []})


def _optional_timestamp(value: str | None) -> datetime | None:
    return parse_timestamp(value) if value else None
