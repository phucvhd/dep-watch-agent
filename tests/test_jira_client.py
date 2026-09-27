import httpx
import pytest

from dep_watch_agent.jira.client import JiraClient


def make_client(handler, **kwargs) -> tuple[JiraClient, list[float]]:
    sleeps: list[float] = []
    http = httpx.Client(base_url="https://jira.test", transport=httpx.MockTransport(handler))
    return JiraClient(http=http, sleep=sleeps.append, **kwargs), sleeps


def search_handler(total: int, requests: list[httpx.Request]):
    """Serve issues KAFKA-1..KAFKA-{total}, honouring startAt/maxResults."""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        start = int(request.url.params["startAt"])
        size = int(request.url.params["maxResults"])
        issues = [{"key": f"KAFKA-{n}"} for n in range(start + 1, min(start + size, total) + 1)]
        return httpx.Response(200, json={"startAt": start, "total": total, "issues": issues})

    return handler


def test_search_paginates():
    requests: list[httpx.Request] = []
    client, _ = make_client(search_handler(25, requests), page_size=10)

    keys = [i["key"] for i in client.search("project = KAFKA", ["summary", "versions"])]

    assert keys == [f"KAFKA-{n}" for n in range(1, 26)]
    assert [r.url.params["startAt"] for r in requests] == ["0", "10", "20"]
    assert requests[0].url.path == "/rest/api/2/search"
    assert requests[0].url.params["jql"] == "project = KAFKA"
    assert requests[0].url.params["fields"] == "summary,versions"


def test_search_empty_result():
    requests: list[httpx.Request] = []
    client, _ = make_client(search_handler(0, requests))
    assert list(client.search("project = NONE", ["summary"])) == []
    assert len(requests) == 1


def test_search_exact_page_multiple_makes_no_extra_request():
    requests: list[httpx.Request] = []
    client, _ = make_client(search_handler(20, requests), page_size=10)
    assert len(list(client.search("x", ["summary"]))) == 20
    assert len(requests) == 2


def test_search_stops_if_server_returns_short_page():
    # total claims more issues than the server actually hands back.
    def handler(request: httpx.Request) -> httpx.Response:
        start = int(request.url.params["startAt"])
        issues = [{"key": "KAFKA-1"}] if start == 0 else []
        return httpx.Response(200, json={"startAt": start, "total": 50, "issues": issues})

    client, _ = make_client(handler)
    assert len(list(client.search("x", ["summary"]))) == 1


def test_delay_between_requests_not_before_first():
    requests: list[httpx.Request] = []
    client, sleeps = make_client(search_handler(25, requests), page_size=10, request_delay=1.5)
    list(client.search("x", ["summary"]))
    assert sleeps == [1.5, 1.5]


def test_retries_429_honouring_retry_after():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json={"startAt": 0, "total": 1, "issues": [{"key": "K-1"}]})

    client, sleeps = make_client(handler, request_delay=0)
    assert [i["key"] for i in client.search("x", ["summary"])] == ["K-1"]
    assert len(calls) == 2
    assert 7.0 in sleeps


def test_retries_5xx_with_exponential_backoff():
    statuses = iter([503, 502, 200])

    def handler(request: httpx.Request) -> httpx.Response:
        status = next(statuses)
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(200, json={"startAt": 0, "total": 0, "issues": []})

    client, sleeps = make_client(handler, request_delay=0, backoff_base=2.0)
    list(client.search("x", ["summary"]))
    backoffs = [s for s in sleeps if s != 0]
    assert backoffs == [2.0, 4.0]


def test_backoff_is_capped():
    client, _ = make_client(lambda r: httpx.Response(200), backoff_base=2.0)
    assert client._backoff(10, None) == 60.0
    assert client._backoff(0, "3600") == 60.0
    assert client._backoff(1, "Wed, 21 Oct 2015 07:28:00 GMT") == 4.0


def test_retries_transport_errors():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) < 3:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={"startAt": 0, "total": 0, "issues": []})

    client, _ = make_client(handler, request_delay=0)
    list(client.search("x", ["summary"]))
    assert len(calls) == 3


def test_gives_up_after_max_retries():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(503)

    client, _ = make_client(handler, request_delay=0, max_retries=3)
    with pytest.raises(httpx.HTTPStatusError):
        list(client.search("x", ["summary"]))
    assert len(calls) == 4


def test_transport_error_raised_after_max_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client, _ = make_client(handler, request_delay=0, max_retries=2)
    with pytest.raises(httpx.ConnectError):
        list(client.search("x", ["summary"]))


def test_client_errors_are_not_retried():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400, json={"errorMessages": ["bad JQL"]})

    client, _ = make_client(handler)
    with pytest.raises(httpx.HTTPStatusError):
        list(client.search("bad", ["summary"]))
    assert len(calls) == 1


def test_comments_paginates():
    all_comments = [{"id": str(n), "body": f"c{n}"} for n in range(1, 8)]
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        start = int(request.url.params["startAt"])
        size = int(request.url.params["maxResults"])
        return httpx.Response(
            200,
            json={"startAt": start, "total": 7, "comments": all_comments[start : start + size]},
        )

    client, _ = make_client(handler, page_size=3)
    assert client.comments("KAFKA-9") == all_comments
    assert requests[0].url.path == "/rest/api/2/issue/KAFKA-9/comment"
    assert [r.url.params["startAt"] for r in requests] == ["0", "3", "6"]
