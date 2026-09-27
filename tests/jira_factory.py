"""Builders for raw JIRA API payloads used across tests."""

from typing import Any


def raw_comment(id: int, body: str, created: str = "2024-01-02T10:00:00.000+0000") -> dict:
    return {
        "id": str(id),
        "author": {"name": "someone", "displayName": "Some One"},
        "body": body,
        "created": created,
        "updated": created,
    }


def raw_issue(
    id: int,
    key: str,
    *,
    summary: str = "Something broke",
    updated: str = "2024-01-05T12:00:00.000+0000",
    affects: list[str] | None = None,
    fix: list[str] | None = None,
    components: list[str] | None = None,
    comments: list[dict] | None = None,
    comment_total: int | None = None,
    **fields: Any,
) -> dict:
    comments = comments or []
    return {
        "id": str(id),
        "key": key,
        "fields": {
            "summary": summary,
            "description": "Steps to reproduce...",
            "issuetype": {"name": "Bug"},
            "status": {"name": "Resolved"},
            "resolution": {"name": "Fixed"},
            "priority": {"name": "Major"},
            "labels": [],
            "components": [{"name": c} for c in components or []],
            "versions": [{"name": v} for v in affects or []],
            "fixVersions": [{"name": v} for v in fix or []],
            "created": "2024-01-01T09:00:00.000+0000",
            "updated": updated,
            "resolutiondate": "2024-01-05T12:00:00.000+0000",
            "comment": {
                "comments": comments,
                "total": len(comments) if comment_total is None else comment_total,
                "startAt": 0,
                "maxResults": len(comments),
            },
            **fields,
        },
    }
