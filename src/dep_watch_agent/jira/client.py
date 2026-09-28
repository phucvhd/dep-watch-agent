"""HTTP client for the Apache JIRA REST API (v2, anonymous access).

Polite by default: a fixed delay between requests, and retries with backoff on 429, 5xx and
network errors, honouring ``Retry-After`` when the server sends it.
"""

import time
from collections.abc import Callable, Iterator
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://issues.apache.org/jira"

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_BACKOFF_SECONDS = 60.0


class JiraClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        page_size: int = 100,
        request_delay: float = 1.0,
        max_retries: int = 5,
        backoff_base: float = 2.0,
        timeout: float = 60.0,
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = http or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": "dep-watch-agent"},
        )
        self.page_size = page_size
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep
        self._has_requested = False

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def search(self, jql: str, fields: list[str]) -> Iterator[dict[str, Any]]:
        """Yield every issue matching ``jql``, following pagination."""
        start_at = 0
        while True:
            page = self._get(
                "/rest/api/2/search",
                {
                    "jql": jql,
                    "fields": ",".join(fields),
                    "startAt": start_at,
                    "maxResults": self.page_size,
                },
            )
            issues = page.get("issues", [])
            yield from issues
            start_at += len(issues)
            if not issues or start_at >= page["total"]:
                return

    def comments(self, issue_key: str) -> list[dict[str, Any]]:
        """Fetch every comment on an issue, for when search results truncate them."""
        comments: list[dict[str, Any]] = []
        while True:
            page = self._get(
                f"/rest/api/2/issue/{issue_key}/comment",
                {"startAt": len(comments), "maxResults": self.page_size},
            )
            batch = page.get("comments", [])
            comments.extend(batch)
            if not batch or len(comments) >= page["total"]:
                return comments

    def project_versions(self, project: str) -> list[dict[str, Any]]:
        """Every version defined in a project, released or not."""
        return self._get(f"/rest/api/2/project/{project}/versions", {})

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        attempt = 0
        while True:
            if self._has_requested:
                self._sleep(self.request_delay)
            self._has_requested = True

            try:
                response = self._http.get(path, params=params)
            except httpx.TransportError:
                if attempt >= self.max_retries:
                    raise
                self._sleep(self._backoff(attempt, None))
                attempt += 1
                continue

            if response.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                self._sleep(self._backoff(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue

            response.raise_for_status()
            return response.json()

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after is not None:
            try:
                return min(float(retry_after), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass  # HTTP-date form; fall back to exponential backoff
        return min(self.backoff_base * 2**attempt, _MAX_BACKOFF_SECONDS)
