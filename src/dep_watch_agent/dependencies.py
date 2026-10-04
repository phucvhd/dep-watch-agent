"""The dependencies the system knows about.

``DEPENDENCIES`` are the ones that can be watched: their issues are synced and answered. Only
Apache Kafka for now (see CLAUDE.md, out of scope: other dependencies).

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


DEPENDENCIES = (
    Dependency(
        id="kafka",
        name="Apache Kafka",
        project="KAFKA",
        tracker_url="https://issues.apache.org/jira/projects/KAFKA",
    ),
)


@dataclass(frozen=True)
class Family:
    id: str
    name: str
    groups: tuple[str, ...]  # Maven group ids (exact, or a prefix ending in ".")
    images: tuple[str, ...] = field(default=())  # container images whose tag is the version

    @property
    def watchable(self) -> bool:
        return any(d.id == self.id for d in DEPENDENCIES)

    def matches_group(self, group: str) -> bool:
        return any(group == g or (g.endswith(".") and group.startswith(g)) for g in self.groups)


FAMILIES = (
    Family(
        "kafka",
        "Apache Kafka",
        ("org.apache.kafka",),
        images=("apache/kafka", "apache/kafka-native", "bitnami/kafka"),
    ),
    Family("spark", "Apache Spark", ("org.apache.spark",)),
    Family("flink", "Apache Flink", ("org.apache.flink",)),
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


def family_for_image(image: str) -> Family | None:
    return next((f for f in FAMILIES if image in f.images), None)
