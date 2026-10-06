import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from dep_watch_agent.api.app import create_app
from dep_watch_agent.api.deps import Settings
from dep_watch_agent.db import migrate
from dep_watch_agent.jira.models import parse_issue
from dep_watch_agent.jira.store import upsert_issue, upsert_versions
from dep_watch_agent.verdict import Evidence, Extraction, IssueText
from tests.eval_factory import ALL_YES, fill_labels
from tests.jira_factory import raw_comment, raw_issue


def raw_version(id: int, name: str, released: bool = True) -> dict:
    return {"id": str(id), "name": name, "released": released, "archived": False}


def bot_comment(id: int, body: str) -> dict:
    return {
        **raw_comment(id, body),
        "author": {"name": "githubbot", "displayName": "ASF GitHub Bot"},
    }


VERSIONS = [
    raw_version(1, "3.10.0"),
    raw_version(2, "3.5.2"),
    raw_version(3, "3.9.0"),
    raw_version(4, "3.6.0"),
    raw_version(5, "4.0.0", released=False),
    raw_version(6, "trunk", released=False),
]

DEADLOCK = raw_issue(
    100,
    "KAFKA-100",
    summary="Consumer deadlock after rebalance",
    description="Regression in 3.6.0: the consumer hangs.",
    affects=["3.6.0"],
    fix=["3.9.0"],
    components=["consumer"],
    comments=[
        raw_comment(1, "Works fine on 3.5.2."),
        # Bot comments are hidden from the system, as in the eval.
        bot_comment(2, "This was introduced in 3.5.2 by the new code path."),
    ],
)
CPU = raw_issue(
    101,
    "KAFKA-101",
    summary="Producer uses 100% CPU",
    components=["producer"],
    created="2024-02-01T09:00:00.000+0000",
    resolution=None,
)


class PhraseExtractor:
    """Cites a fact for each known phrase in the issue text, quoting the field it is in."""

    PHRASES = {
        "Regression in 3.6.0": ("3.6.0", "introduced"),
        "Works fine on 3.5.2": ("3.5.2", "unaffected"),
        "introduced in 3.5.2": ("3.5.2", "introduced"),
    }

    def extract(self, issue: IssueText) -> Extraction:
        return Extraction(
            [
                Evidence(version, kind, text)
                for text in issue.fields()
                for phrase, (version, kind) in self.PHRASES.items()
                if phrase in text
            ]
        )


# Registered under two names: the name in results is the key, not anything on the class.
SYSTEMS = {"phrases": PhraseExtractor, "phrases-2": PhraseExtractor}


@pytest.fixture
def sessions(schema):
    migrate(schema.url, schema=schema.name)
    factory = sessionmaker(schema.engine())
    with factory() as session:
        upsert_versions(session, "KAFKA", VERSIONS)
        upsert_issue(session, parse_issue(DEADLOCK))
        upsert_issue(session, parse_issue(CPU))
        session.commit()
    return factory


@pytest.fixture
def make_client(sessions, tmp_path):
    def make(datasets_dir=None, **deps) -> TestClient:
        deps.setdefault("systems", SYSTEMS)
        settings = Settings(
            datasets_dir=datasets_dir or tmp_path / "datasets",
            runs_dir=tmp_path / "runs",
            cors_origins=["http://localhost:5173"],
            migrate_on_startup=False,
        )
        return TestClient(create_app(settings=settings, sessions=sessions, **deps))

    return make


@pytest.fixture
def client(make_client):
    return make_client()


def wait(client: TestClient, job: dict) -> dict:
    client.app.state.jobs.wait(job["id"], timeout=10)
    return client.get(f"/jobs/{job['id']}").json()


# --- ops ---------------------------------------------------------------------------------


def test_health_reports_db_revision(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["db_revision"]


def test_cors_allows_the_frontend(client):
    response = client.options(
        "/issues",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_dependencies_are_listed(client):
    catalog = client.get("/dependencies").json()
    kafka, spark, hadoop = catalog[:3]  # the order fixes each source's color
    assert (kafka["id"], kafka["name"], kafka["project"]) == ("kafka", "Apache Kafka", "KAFKA")
    assert kafka["watchable"]
    assert (spark["project"], spark["watchable"]) == ("SPARK", False)  # synced, not answered
    assert (hadoop["project"], hadoop["watchable"]) == ("HADOOP", False)
    assert {"FLINK", "CASSANDRA"} <= {d["project"] for d in catalog}
    # Only Kafka's issues are in the test database: the rest are in the catalog, not added.
    assert [d["project"] for d in catalog if d["added"]] == ["KAFKA"]


def test_sources_count_issues_per_dependency(client):
    kafka, spark, hadoop, *_ = client.get("/stats/sources").json()
    assert (kafka["issues"], kafka["bugs"], kafka["open_bugs"], kafka["added"]) == (2, 2, 1, True)
    assert (spark["name"], spark["issues"], spark["synced_at"]) == ("Apache Spark", 0, None)
    assert spark["added"] is False
    assert hadoop["dependency"] == "hadoop"


def test_repo_scan_reads_manifests_only(client):
    lockfile = "org.apache.kafka:kafka-clients:3.9.1=runtimeClasspath\n"
    sbt = '"org.apache.spark" %% "spark-sql" % "3.5.1"\n'
    response = client.post(
        "/repo/scan",
        json={
            "files": [
                {"path": "gradle.lockfile", "content": lockfile},
                {"path": "build.sbt", "content": sbt},
                {"path": "/etc/passwd", "content": "root:x:0:0"},  # not a manifest: ignored
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["files_read"] == ["gradle.lockfile", "build.sbt"]
    kafka, spark = body["dependencies"]
    assert (kafka["key"], kafka["version"], kafka["watchable"]) == ("kafka", "3.9.1", True)
    assert (kafka["ecosystem"], kafka["notes"]) == ("maven", [])
    assert (spark["name"], spark["watchable"], spark["reason"]) == (
        "Apache Spark",
        False,
        "Not supported yet",
    )


def test_repo_scan_limits_its_input(client):
    too_many = [{"path": "pom.xml", "content": ""}] * 501
    assert client.post("/repo/scan", json={"files": too_many}).status_code == 422


def test_systems_lists_the_default_first(client, make_client):
    assert client.get("/systems").json() == ["phrases", "phrases-2"]
    assert make_client(systems={}).get("/systems").json() == []


def test_openapi_schema_is_served(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/check", "/issues", "/sync/jira", "/eval/runs"} <= set(paths)


# --- issues and versions -----------------------------------------------------------------


def test_list_issues_newest_first(client):
    body = client.get("/issues", params={"project": "KAFKA"}).json()
    assert body["total"] == 2
    assert [i["key"] for i in body["items"]] == ["KAFKA-101", "KAFKA-100"]
    assert body["items"][1]["url"] == "https://issues.apache.org/jira/browse/KAFKA-100"


@pytest.mark.parametrize(
    ("params", "keys"),
    [
        ({"q": "deadlock"}, ["KAFKA-100"]),
        ({"q": "kafka-101"}, ["KAFKA-101"]),
        ({"q": "100%"}, ["KAFKA-101"]),  # % is literal, not a wildcard
        ({"component": "consumer"}, ["KAFKA-100"]),
        ({"fix_version": "3.9.0"}, ["KAFKA-100"]),
        ({"affects_version": "3.9.0"}, []),
        ({"resolution": "Fixed"}, ["KAFKA-100"]),
    ],
)
def test_list_issues_filters(client, params, keys):
    assert [
        i["key"]
        for i in client.get("/issues", params={"project": "KAFKA", **params}).json()["items"]
    ] == keys


def test_list_issues_paginates(client):
    body = client.get("/issues", params={"project": "KAFKA", "limit": 1, "offset": 1}).json()
    assert body["total"] == 2
    assert [i["key"] for i in body["items"]] == ["KAFKA-100"]


def test_list_issues_rejects_bad_project(client):
    assert client.get("/issues", params={"project": 'KAFKA" OR 1=1'}).status_code == 422


def test_get_issue(client):
    body = client.get("/issues/KAFKA-100").json()
    assert body["fix_versions"] == ["3.9.0"]
    assert body["components"] == ["consumer"]
    assert [c["body"] for c in body["comments"]][0] == "Works fine on 3.5.2."


def test_get_missing_issue(client):
    assert client.get("/issues/KAFKA-999").status_code == 404


def test_versions_are_ordered_numerically(client):
    names = [v["name"] for v in client.get("/versions", params={"project": "KAFKA"}).json()]
    assert names == ["3.5.2", "3.6.0", "3.9.0", "3.10.0", "4.0.0", "trunk"]
    released = [
        v["name"]
        for v in client.get("/versions", params={"project": "KAFKA", "released": True}).json()
    ]
    assert released == ["3.5.2", "3.6.0", "3.9.0", "3.10.0"]


# --- check -------------------------------------------------------------------------------


def check(client, version, key="KAFKA-100", **extra):
    return client.post("/check", json={"issue_key": key, "version": version, **extra})


def test_check_affected_cites_the_issue(client):
    body = check(client, "3.6.0").json()
    assert body["answer"] == "affected"
    assert body["system"] == "phrases"  # the first registered system
    assert body["url"] == "https://issues.apache.org/jira/browse/KAFKA-100"
    assert body["fix_versions"] == ["3.9.0"]
    assert body["decided_by"] == "phrases"
    assert {"version": "3.6.0", "kind": "introduced", "quote": DEADLOCK_QUOTE} in body["evidence"]


class VersionedPhraseExtractor(PhraseExtractor):
    version = "v1"


def test_check_reuses_stored_facts(make_client):
    client = make_client(systems={"phrases": VersionedPhraseExtractor})
    assert check(client, "3.6.0").json()["cached"] is False
    body = check(client, "3.6.1").json()  # another version, same facts
    assert (body["cached"], body["answer"]) == (True, "affected")


def test_check_past_the_fix_is_decided_by_code(client):
    body = check(client, "3.9.0").json()
    assert (body["answer"], body["decided_by"]) == ("not_affected", "fix_versions")


DEADLOCK_QUOTE = "Regression in 3.6.0: the consumer hangs."


@pytest.mark.parametrize(
    ("version", "answer"),
    [
        ("3.5.2", "not_affected"),  # the bot's "introduced in 3.5.2" isn't visible
        ("3.9.0", "not_affected"),
        ("3.10.0", "not_affected"),  # 3.10.0 > 3.9.0, numerically
    ],
)
def test_check_decides_by_version(client, version, answer):
    assert check(client, version).json()["answer"] == answer


def test_check_without_evidence_abstains(client):
    body = check(client, "3.6.0", key="KAFKA-101").json()
    assert body["answer"] == "insufficient_information"
    assert body["evidence"] == []


@pytest.mark.parametrize("version", ["3.7", "banana", ""])
def test_check_needs_a_specific_release(client, version):
    assert check(client, version).status_code == 422


def test_check_missing_issue(client):
    assert check(client, "3.6.0", key="KAFKA-999").status_code == 404
    assert check(client, "3.6.0", key="not-a-key").status_code == 422


def test_check_reports_the_registered_name(client):
    assert check(client, "3.6.0", system="phrases-2").json()["system"] == "phrases-2"


def test_check_unknown_system(client):
    response = check(client, "3.6.0", system="baseline")
    assert response.status_code == 422
    assert "phrases" in response.json()["detail"]


def test_check_needs_a_registered_system(make_client):
    response = check(make_client(systems={}), "3.6.0")
    assert response.status_code == 503


# --- scan --------------------------------------------------------------------------------


def scan(client, **body):
    return client.post("/scan", json={"project": "KAFKA", "version": "3.6.0", **body})


def test_scan_answers_each_issue(client):
    response = scan(client)
    assert response.status_code == 202
    job = wait(client, response.json())

    assert job["status"] == "succeeded", job["error"]
    assert job["params"]["system"] == "phrases"
    result = job["result"]
    assert result["counts"] == {"affected": 1, "not_affected": 0, "insufficient_information": 1}
    assert result["candidates_total"] == result["scanned"] == 2
    assert result["errors"] == 0
    affected, vague = result["items"]
    assert (affected["issue_key"], affected["answer"]) == ("KAFKA-100", "affected")
    assert affected["url"] == "https://issues.apache.org/jira/browse/KAFKA-100"
    assert affected["evidence"][0]["quote"] == DEADLOCK_QUOTE
    assert (vague["issue_key"], vague["answer"]) == ("KAFKA-101", "insufficient_information")


def test_scan_past_the_fix(client):
    job = wait(client, scan(client, version="3.10.0").json())
    deadlock = next(i for i in job["result"]["items"] if i["issue_key"] == "KAFKA-100")
    assert (deadlock["answer"], deadlock["decided_by"]) == ("not_affected", "fix_versions")


def test_scan_since_filters_by_update_time(client):
    job = wait(client, scan(client, since="2030-01-01T00:00:00Z").json())
    assert job["result"]["items"] == []


def test_scan_backlog_counts_without_a_model_call(make_client):
    client = make_client(systems={"phrases": CountingPhrases})
    CountingPhrases.calls = 0
    params = {"project": "KAFKA", "version": "3.6.0"}
    before = client.get("/scan/backlog", params=params).json()
    assert (before["candidates"], before["settled"], before["checked"], before["unchecked"]) == (
        2,
        0,
        0,
        2,
    )
    check(client, "3.6.0")  # reads KAFKA-100
    after = client.get("/scan/backlog", params=params).json()
    assert (after["checked"], after["unchecked"], after["system"]) == (1, 1, "phrases")
    assert CountingPhrases.calls == 1
    assert client.get("/scan/backlog", params={**params, "version": "3.6"}).status_code == 422


def test_scan_answers_only_watchable_dependencies(client):
    response = scan(client, project="SPARK", version="3.5.1")
    assert response.status_code == 422
    assert "not supported for checks" in response.json()["detail"]
    assert scan(client, project="NOPE").status_code == 422


def test_scan_validates_its_request(client, make_client):
    assert scan(client, version="3.6").status_code == 422
    assert scan(client, limit=0).status_code == 422
    assert scan(client, system="nope").status_code == 422
    assert scan(make_client(systems={}), version="3.6.0").status_code == 503


# --- sync --------------------------------------------------------------------------------


class FakeJira:
    def __init__(self, issues, release: threading.Event | None = None):
        self.issues = issues
        self.release = release
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def project_versions(self, project):
        return []

    def search(self, jql, fields):
        if self.release is not None:
            self.release.wait(10)
        yield from self.issues

    def comments(self, key):
        return []


def test_sync_runs_as_a_job(make_client):
    fake = FakeJira([raw_issue(200, "KAFKA-200")])
    client = make_client(jira_client_factory=fake)

    response = client.post("/sync/jira", json={"project": "KAFKA", "request_delay": 2})
    assert response.status_code == 202
    job = wait(client, response.json())

    assert job["status"] == "succeeded", job["error"]
    assert job["result"]["issues_synced"] == 1
    assert job["progress"] == 1
    assert fake.kwargs == {"request_delay": 2}
    assert client.get("/issues/KAFKA-200").status_code == 200
    assert [s["source"] for s in client.get("/sync/state").json()] == ["jira:KAFKA"]


def test_sync_runs_are_listed_newest_first(make_client):
    client = make_client(jira_client_factory=FakeJira([raw_issue(200, "KAFKA-200")]))
    for _ in range(2):
        wait(client, client.post("/sync/jira", json={"project": "KAFKA"}).json())

    runs = client.get("/sync/runs", params={"project": "KAFKA"}).json()
    assert [(r["status"], r["fetched"], r["new_issues"]) for r in runs] == [
        ("succeeded", 1, 0),  # the second sync: the issue was already there
        ("succeeded", 1, 1),
    ]
    assert client.get("/sync/runs", params={"project": "SPARK"}).json() == []


def test_second_sync_of_a_project_is_a_conflict(make_client):
    release = threading.Event()
    client = make_client(jira_client_factory=FakeJira([], release=release))
    first = client.post("/sync/jira", json={"project": "KAFKA"}).json()

    response = client.post("/sync/jira", json={"project": "KAFKA", "full": True})
    assert response.status_code == 409
    assert response.json()["job"]["id"] == first["id"]  # the frontend can poll the running one

    release.set()
    assert wait(client, first)["status"] == "succeeded"


def test_sync_failure_is_reported_on_the_job(make_client):
    class Broken(FakeJira):
        def search(self, jql, fields):
            raise RuntimeError("JIRA is down")

    client = make_client(jira_client_factory=Broken([]))
    job = wait(client, client.post("/sync/jira", json={"project": "KAFKA"}).json())
    assert job["status"] == "failed"
    assert "JIRA is down" in job["error"]


def test_sync_rejects_request_delays_that_hammer_jira(client):
    assert (
        client.post("/sync/jira", json={"project": "KAFKA", "request_delay": 0}).status_code == 422
    )


def test_unknown_job(client):
    assert client.get("/jobs/nope").status_code == 404


# --- eval --------------------------------------------------------------------------------


@pytest.fixture
def eval_client(make_client, written):
    return make_client(datasets_dir=written.parent)


def test_list_datasets(eval_client):
    assert eval_client.get("/eval/datasets").json() == [
        {"name": "test-set", "design": "v1", "labeled": 0, "total": 4}
    ]


def test_dataset_status(eval_client, written):
    body = eval_client.get("/eval/datasets/test-set/status").json()
    assert (body["labeled"], body["total"], body["ready"]) == (0, 4, False)
    assert body["problems"] == []  # unlabeled cases aren't listed as problems

    fill_labels(written, ALL_YES)
    assert eval_client.get("/eval/datasets/test-set/status").json()["ready"] is True


def test_missing_dataset(eval_client):
    assert eval_client.get("/eval/datasets/nope/status").status_code == 404


def test_sampling_refuses_to_overwrite_labels(eval_client):
    response = eval_client.post("/eval/datasets", json={"name": "test-set"})
    assert response.status_code == 409


def test_path_traversal_is_rejected(eval_client):
    assert eval_client.get("/eval/datasets/..%2Fsecrets/status").status_code in (404, 422)
    assert eval_client.get("/eval/runs/test-set/.hidden").status_code == 422
    assert eval_client.post("/eval/datasets", json={"name": "../x"}).status_code == 422


def run_body(**fields) -> dict:
    return {"dataset": "test-set", "system": "phrases", **fields}


def test_run_needs_labels_unless_provisional(eval_client):
    response = eval_client.post("/eval/runs", json=run_body())
    assert response.status_code == 400
    assert "provisional" in response.json()["detail"]


def test_run_needs_a_registered_system(eval_client):
    body = run_body(provisional=True)
    assert eval_client.post("/eval/runs", json={**body, "system": "baseline"}).status_code == 422
    del body["system"]
    assert eval_client.post("/eval/runs", json=body).status_code == 422


def test_provisional_runs_are_local_only(eval_client):
    body = run_body(provisional=True, langfuse=True)
    assert eval_client.post("/eval/runs", json=body).status_code == 400


def test_provisional_run_saves_results(eval_client):
    body = run_body(provisional=True, run_name="t1")
    response = eval_client.post("/eval/runs", json=body)
    assert response.status_code == 202
    job = wait(eval_client, response.json())

    assert job["status"] == "succeeded", job["error"]
    assert job["result"]["system"] == "phrases"
    assert job["result"]["metrics"]["n"] == 4
    runs = eval_client.get("/eval/runs").json()
    assert [(r["run_name"], r["provisional"]) for r in runs] == [("t1", True)]
    assert "results" not in runs[0]
    run = eval_client.get("/eval/runs/test-set/t1").json()
    assert len(run["results"]) == 4
    assert eval_client.get("/eval/runs/test-set/t2").status_code == 404


def test_run_is_named_after_the_registered_system(eval_client):
    response = eval_client.post("/eval/runs", json=run_body(system="phrases-2", provisional=True))
    job = wait(eval_client, response.json())

    assert job["status"] == "succeeded", job["error"]
    assert job["result"]["system"] == "phrases-2"
    assert job["result"]["run_name"].startswith("phrases-2-")
    run = eval_client.get(f"/eval/runs/test-set/{job['result']['run_name']}").json()
    assert run["system"] == "phrases-2"


class FakeLangfuse:
    def __init__(self):
        self.items = []

    def create_dataset(self, **kwargs):
        pass

    def create_dataset_item(self, **kwargs):
        self.items.append(kwargs)

    def flush(self):
        pass


def test_upload_needs_labels(make_client, written):
    fake = FakeLangfuse()
    client = make_client(datasets_dir=written.parent, langfuse_factory=lambda: fake)
    assert client.post("/eval/datasets/test-set/upload").status_code == 400

    fill_labels(written, ALL_YES)
    assert client.post("/eval/datasets/test-set/upload").json() == {
        "name": "test-set",
        "uploaded": 4,
    }
    assert len(fake.items) == 4


# --- stored answers and stats ------------------------------------------------------------


class CountingPhrases(PhraseExtractor):
    version = "v1"
    calls = 0

    def extract(self, issue):
        CountingPhrases.calls += 1
        return super().extract(issue)


def answer(client, key="KAFKA-100", version="3.6.0"):
    return client.get(f"/issues/{key}/answer", params={"version": version})


def test_stored_answer_never_calls_the_model(make_client):
    client = make_client(systems={"phrases": CountingPhrases})
    CountingPhrases.calls = 0

    body = answer(client).json()
    assert (body["answered"], body["system"], body["result"]) == (False, "phrases", None)

    # Past the fix, code answers without stored facts.
    past = answer(client, version="3.9.0").json()
    assert past["answered"] and past["result"]["decided_by"] == "fix_versions"

    # Once /check has read the issue, its stored facts answer any version.
    check(client, "3.6.0")
    assert CountingPhrases.calls == 1
    stored = answer(client, version="3.6.1").json()
    assert stored["answered"] and stored["result"]["answer"] == "affected"
    assert stored["result"]["cached"] is True
    assert CountingPhrases.calls == 1  # no further model call
    assert client.get("/stats/issues", params={"project": "KAFKA"}).json()["read"] == 1


class DownExtractor:
    def extract(self, issue):
        raise ConnectionError("Connection error.")


def test_check_reports_a_model_server_failure(make_client):
    response = check(make_client(systems={"down": DownExtractor}), "3.6.0")
    assert response.status_code == 502
    assert response.json()["detail"] == "down could not read the issue: Connection error."


def test_recheck_reads_the_issue_again(make_client):
    client = make_client(systems={"phrases": CountingPhrases})
    CountingPhrases.calls = 0
    check(client, "3.6.0")
    assert check(client, "3.6.0").json()["cached"] is True
    assert CountingPhrases.calls == 1

    again = check(client, "3.6.0", refresh=True).json()
    assert (again["answer"], again["cached"]) == ("affected", False)
    assert CountingPhrases.calls == 2

    # Past the fix the fix versions answer; a re-check doesn't call the model.
    past = check(client, "3.9.0", refresh=True).json()
    assert past["decided_by"] == "fix_versions"
    assert CountingPhrases.calls == 2


def test_stored_answers_for_a_page_of_issues(make_client):
    client = make_client(systems={"phrases": CountingPhrases})
    CountingPhrases.calls = 0
    check(client, "3.6.0", key="KAFKA-100")
    keys = ["KAFKA-101", "KAFKA-100", "KAFKA-999"]
    body = client.get("/answers", params={"version": "3.6.1", "key": keys}).json()

    assert (body["version"], body["system"]) == ("3.6.1", "phrases")
    assert [i["issue_key"] for i in body["items"]] == keys  # in the order asked
    unread, read, missing = body["items"]
    assert (unread["answered"], missing["answered"]) == (False, False)
    assert read["answered"] and read["result"]["answer"] == "affected"
    assert CountingPhrases.calls == 1  # never a model call


def test_stored_answers_validate_the_version(client):
    params = {"version": "3.6", "key": ["KAFKA-100"]}
    assert client.get("/answers", params=params).status_code == 422
    assert (
        client.get("/answers", params={"version": "3.6.0", "key": ["not a key"]}).status_code == 422
    )


def test_stored_answer_without_a_model(make_client):
    client = make_client(systems={})
    assert answer(client).json() == {"answered": False, "system": None, "result": None}
    assert answer(client, version="3.9.0").json()["answered"] is True
    assert answer(client, key="KAFKA-999").status_code == 404
    assert answer(client, version="3.6").status_code == 422


def test_activity_counts_new_and_resolved_issues(client):
    # DEADLOCK: created 2024-01-01, resolved 2024-01-05. CPU: created 2024-02-01, open.
    body = client.get(
        "/stats/activity",
        params={"project": "KAFKA", "days": 35, "now": "2024-02-03T12:00:00Z"},
    ).json()
    days = {d["day"]: d for d in body["days"]}
    assert len(body["days"]) == 35
    assert (body["days"][0]["day"], body["days"][-1]["day"]) == ("2023-12-31", "2024-02-03")
    assert days["2024-01-01"] == {"day": "2024-01-01", "created": 1, "bugs": 1, "resolved": 0}
    assert days["2024-01-05"]["resolved"] == 1
    assert days["2024-02-01"]["created"] == 1
    assert (body["new_24h"], body["new_7d"], body["new_30d"]) == (0, 1, 1)
    assert body["by_type"] == [{"issue_type": "Bug", "count": 2}]


def test_issue_stats(client):
    stats = client.get("/stats/issues", params={"project": "KAFKA"}).json()
    assert (stats["total"], stats["bugs"], stats["open_bugs"], stats["fixed_bugs"]) == (2, 2, 1, 1)
    assert stats["read"] == 0
    assert stats["newest"].startswith("2024-01-05")


def test_monthly_bugs_filed_and_fixed(client):
    rows = client.get(
        "/stats/issues/monthly",
        params={"project": "KAFKA", "months": 3, "now": "2024-02-15T00:00:00Z"},
    ).json()
    # DEADLOCK: created 2024-01-01, resolved (Fixed) 2024-01-05. CPU: created 2024-02-01, open.
    assert rows == [
        {"month": "2023-12", "filed": 0, "fixed": 0},
        {"month": "2024-01", "filed": 1, "fixed": 1},
        {"month": "2024-02", "filed": 1, "fixed": 0},
    ]


def test_reading_time(make_client):
    client = make_client(systems={"phrases": CountingPhrases})
    empty = client.get("/stats/reading", params={"project": "KAFKA"}).json()
    assert (empty["count"], empty["median_ms"], len(empty["bins"])) == (0, None, 8)
    check(client, "3.6.0")
    stats = client.get("/stats/reading", params={"project": "KAFKA"}).json()
    assert stats["count"] == 1
    assert stats["bins"][0]["count"] == 1  # a fake reads in well under 15 s
    assert stats["bins"][-1]["to_s"] is None
