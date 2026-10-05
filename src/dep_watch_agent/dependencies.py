"""The dependencies the system knows about.

``DEPENDENCIES`` are the ones whose issues are synced. Only ``watchable`` ones are answered
(scans, checks, the eval): the prompt, the version scheme and the ground truth are Kafka's.
Spark and Hadoop are synced for the overview only, a scope decision of 2026-10-04.

``FAMILIES`` names the artifacts a repository scan recognizes, so a scan can say "Apache Spark
3.5.1" instead of listing ``org.apache.spark:spark-core_2.12`` and its siblings. A family is
watchable only if its ``watch`` id is in ``DEPENDENCIES``; the others are shown, not watched.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dependency:
    id: str
    name: str
    project: str  # the JIRA project its issues are synced from
    tracker_url: str
    watchable: bool = True  # answered for a version, not only synced


DEPENDENCIES = (
    Dependency(
        id="kafka",
        name="Apache Kafka",
        project="KAFKA",
        tracker_url="https://issues.apache.org/jira/projects/KAFKA",
    ),
    Dependency(
        id="spark",
        name="Apache Spark",
        project="SPARK",
        tracker_url="https://issues.apache.org/jira/projects/SPARK",
        watchable=False,
    ),
    Dependency(
        id="hadoop",
        name="Apache Hadoop",
        project="HADOOP",  # Hadoop Common; HDFS, YARN and MapReduce are projects of their own
        tracker_url="https://issues.apache.org/jira/projects/HADOOP",
        watchable=False,
    ),
)


@dataclass(frozen=True)
class Family:
    id: str
    name: str
    groups: tuple[str, ...]  # Maven group ids (exact, or a prefix ending in ".")
    images: tuple[str, ...] = field(default=())  # container images whose tag is the version
    packages: tuple[str, ...] = field(default=())  # "pypi:name" / "npm:name" at the same version

    @property
    def watchable(self) -> bool:
        return any(d.id == self.id and d.watchable for d in DEPENDENCIES)

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
