from sqlalchemy.orm import sessionmaker

from dep_watch_agent.db import migrate
from dep_watch_agent.llm.extractor import LLMExtractor, load_prompt
from dep_watch_agent.orm import IssuePassageRow
from dep_watch_agent.retrieval import (
    HybridExtractor,
    HybridRetriever,
    Passage,
    Ranked,
    lexical_query,
    passages,
    releases_named,
    select_within,
)
from dep_watch_agent.verdict import IssueText

LONG = IssueText(
    summary="Broker crash",
    description="Stack trace follows.\n\n" + "at org.apache.kafka.Foo\n" * 30,
    comments=[
        "Unrelated chatter about tests.",
        "This is a regression since 3.6.0; 3.5.2 works.",
        "Thanks, merged.",
    ],
    fix_versions=["3.7.1"],
)


def test_passages_split_paragraphs_and_long_text():
    items = passages(LONG, max_chars=200)
    assert items[0] == Passage(0, "description", "Stack trace follows.")
    assert all(len(p.body) <= 200 for p in items)
    assert [p.field for p in items[-3:]] == ["comment"] * 3
    assert [p.position for p in items] == list(range(len(items)))


def test_lexical_query_names_the_issues_releases():
    assert releases_named(LONG) == ["3.6.0", "3.5.2", "3.7.1"]
    query = lexical_query(LONG)
    assert "regression | " in query and query.endswith("3.6.0 | 3.5.2 | 3.7.1")


def test_select_within_keeps_issue_order_and_budget():
    ranked = [
        Ranked(Passage(2, "comment", "c" * 50), 0.9),
        Ranked(Passage(0, "description", "d" * 80), 0.8),  # too big once c is in
        Ranked(Passage(1, "comment", "e" * 40), 0.7),
    ]
    assert [p.position for p in select_within(ranked, 100)] == [1, 2]


class FakeEmbedder:
    """2-d embeddings: passages naming a version point the way the version question does."""

    model = "fake-embed"

    def __init__(self):
        self.embedded = []

    def embed(self, texts):
        self.embedded.extend(texts)
        return [[1.0, 0.0] if ("since" in t or "Query" in t) else [0.0, 1.0] for t in texts]


class Recorder:
    def __init__(self):
        self.users = []

    def __call__(self, system, user):
        self.users.append(user)
        return {
            "evidence": [
                {"version": "3.6.0", "kind": "introduced", "quote": "regression since 3.6.0"}
            ]
        }


def test_hybrid_ranks_in_postgres_and_reads_the_best_passages(schema):
    migrate(schema.url, schema=schema.name)
    sessions = sessionmaker(schema.engine())
    embedder = FakeEmbedder()
    retriever = HybridRetriever(sessions, embedder)

    ranked = retriever.rank("K-1", LONG)
    assert "regression since 3.6.0" in ranked[0].passage.body
    first_pass = len(embedder.embedded)
    retriever.rank("K-1", LONG)  # stored passages are reused
    assert len(embedder.embedded) == first_pass
    with sessions() as session:
        assert session.query(IssuePassageRow).filter_by(issue_key="K-1").count() == len(
            passages(LONG)
        )

    model = Recorder()
    base = LLMExtractor(model, prompt=load_prompt(), model_id="m")
    hybrid = HybridExtractor(base, retriever, budget_chars=120)
    extraction = hybrid.extract(LONG)
    assert [e.version for e in extraction.evidence] == ["3.6.0"]
    assert "<comment>\nThis is a regression since 3.6.0; 3.5.2 works.\n</comment>" in model.users[0]
    assert "at org.apache.kafka.Foo" not in model.users[0]
    assert extraction.context[0] == "Broker crash"
    assert "retrieval=hybrid-1@fake-embed;budget=120" in hybrid.version


def test_hybrid_reads_a_short_issue_whole():
    model = Recorder()
    base = LLMExtractor(model, prompt=load_prompt(), model_id="m")
    hybrid = HybridExtractor(base, retriever=None, budget_chars=10_000)  # type: ignore[arg-type]
    extraction = hybrid.extract(LONG)
    assert extraction.context is None
    assert "at org.apache.kafka.Foo" in model.users[0]
