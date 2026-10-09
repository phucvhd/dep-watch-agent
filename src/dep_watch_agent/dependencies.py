"""The dependencies the system knows about.

``DEPENDENCIES`` is the catalog of sources: dependencies whose issues can be synced, each with
the scheme its releases are numbered in. A user adds one by syncing it (``added`` in the API).
Catalog order fixes each source's color in the UI, so new entries go at the end.

A dependency is answered for a version (scans, checks, upgrades) only with an ``Adapter``: the
parts that differ per dependency, such as its extraction prompt. Everything else (the version
module, ``verdict.decide``, stored extractions, the API) is shared. The others are synced for
the overview only (a scope decision of 2026-10-04). An adapter without a ground-truth dataset is
``experimental``: answered, but its answers have not been measured (Spark, from 2026-10-08).

``FAMILIES`` names the artifacts a repository scan recognizes, so a scan can say "Apache Spark
3.5.1" instead of listing ``org.apache.spark:spark-core_2.12`` and its siblings. A family is
watchable only if its dependency is; the others are shown, not watched.
"""

from dataclasses import dataclass, field

from dep_watch_agent.versions import KAFKA, THREE_PART, VersionScheme


@dataclass(frozen=True)
class Adapter:
    """What a dependency needs, beyond its catalog entry, to be answered for a version."""

    prompt: str  # the extraction prompt, ``llm/prompts/<prompt>.md``
    dataset: str | None = None  # its ground truth in Langfuse; None until there is one
    # Other products with releases in the same tracker, by version-name prefix (Spark's JIRA
    # has "kubernetes-operator-1.0.0"). An issue only they have versions in isn't a candidate.
    subprojects: tuple[str, ...] = ()

    @property
    def experimental(self) -> bool:
        """Answered before its ground truth exists, so its answers are unmeasured."""
        return self.dataset is None


@dataclass(frozen=True)
class Dependency:
    id: str
    name: str
    project: str  # the JIRA project its issues are synced from
    tracker_url: str
    scheme: VersionScheme = THREE_PART
    adapter: Adapter | None = None

    @property
    def watchable(self) -> bool:
        """Answered for a version, not only synced."""
        return self.adapter is not None

    @property
    def experimental(self) -> bool:
        return self.adapter is not None and self.adapter.experimental


DEPENDENCIES = (
    Dependency(
        id="kafka",
        name="Apache Kafka",
        project="KAFKA",
        tracker_url="https://issues.apache.org/jira/projects/KAFKA",
        scheme=KAFKA,
        adapter=Adapter(prompt="extract_facts", dataset="kafka-ground-truth-v2"),
    ),
    Dependency(
        id="spark",
        name="Apache Spark",
        project="SPARK",
        tracker_url="https://issues.apache.org/jira/projects/SPARK",
        adapter=Adapter(
            prompt="extract_facts_spark",
            subprojects=(
                "kubernetes-operator-",
                "connect-swift-",
                "connect-rust-",
                "connect-gateway-",
            ),
        ),
    ),
    Dependency(
        id="hadoop",
        name="Apache Hadoop",
        project="HADOOP",  # Hadoop Common; HDFS, YARN and MapReduce are projects of their own
        tracker_url="https://issues.apache.org/jira/projects/HADOOP",
    ),
    # Apache projects still tracked in JIRA (checked 2026-10-05). Parquet and Beam moved their
    # issues to GitHub, so their JIRA projects are frozen and left out.
    *(
        Dependency(
            id=project.lower(),
            name=name,
            project=project,
            tracker_url=f"https://issues.apache.org/jira/projects/{project}",
        )
        for project, name in (
            ("FLINK", "Apache Flink"),
            ("ZOOKEEPER", "Apache ZooKeeper"),
            ("CASSANDRA", "Apache Cassandra"),
            ("HIVE", "Apache Hive"),
            ("HBASE", "Apache HBase"),
            ("AVRO", "Apache Avro"),
        )
    ),
)


def dependency_for_project(project: str) -> Dependency | None:
    return next((d for d in DEPENDENCIES if d.project == project), None)


def scheme_for_project(project: str) -> VersionScheme:
    """The scheme to order a project's versions by; three-part for a project not listed."""
    dependency = dependency_for_project(project)
    return dependency.scheme if dependency else THREE_PART


@dataclass(frozen=True)
class Family:
    id: str
    name: str
    groups: tuple[str, ...]  # Maven group ids (exact, or a prefix ending in ".")
    images: tuple[str, ...] = field(default=())  # container images whose tag is the version
    packages: tuple[str, ...] = field(default=())  # "pypi:name" / "npm:name" at the same version

    @property
    def dependency(self) -> Dependency | None:
        return next((d for d in DEPENDENCIES if d.id == self.id), None)

    @property
    def watchable(self) -> bool:
        return self.dependency is not None and self.dependency.watchable

    @property
    def scheme(self) -> VersionScheme:
        return self.dependency.scheme if self.dependency else THREE_PART

    def matches_group(self, group: str) -> bool:
        return any(group == g or (g.endswith(".") and group.startswith(g)) for g in self.groups)


FAMILIES = (
    Family(
        "kafka",
        "Apache Kafka",
        ("org.apache.kafka",),
        # Confluent's cp-kafka / cp-server are read as the Kafka release they ship (manifests.py).
        images=(
            "apache/kafka",
            "apache/kafka-native",
            "bitnami/kafka",
            "confluentinc/cp-kafka",
            "confluentinc/cp-server",
        ),
    ),
    Family("spark", "Apache Spark", ("org.apache.spark",), packages=("pypi:pyspark",)),
    Family("flink", "Apache Flink", ("org.apache.flink",), packages=("pypi:apache-flink",)),
    Family("hadoop", "Apache Hadoop", ("org.apache.hadoop",)),
    Family("zookeeper", "Apache ZooKeeper", ("org.apache.zookeeper",)),
    Family("cassandra", "Apache Cassandra", ("org.apache.cassandra",)),
    Family("hive", "Apache Hive", ("org.apache.hive",)),
    Family("hbase", "Apache HBase", ("org.apache.hbase",)),
    Family("avro", "Apache Avro", ("org.apache.avro",)),
    Family("pulsar", "Apache Pulsar", ("org.apache.pulsar",)),
    Family("beam", "Apache Beam", ("org.apache.beam",)),
    Family("iceberg", "Apache Iceberg", ("org.apache.iceberg",)),
    Family("parquet", "Apache Parquet", ("org.apache.parquet",)),
    Family("confluent", "Confluent Platform", ("io.confluent",)),
)


def family_for_group(group: str) -> Family | None:
    return next((f for f in FAMILIES if f.matches_group(group)), None)


def family_for(group: str, artifact: str) -> Family | None:
    """The family of a declared dependency: by image, by package, or by Maven group."""
    if group == "image":
        return family_for_image(artifact)
    if group in ("pypi", "npm"):
        return next((f for f in FAMILIES if f"{group}:{artifact}" in f.packages), None)
    return family_for_group(group)


def family_for_image(image: str) -> Family | None:
    return next((f for f in FAMILIES if image in f.images), None)
