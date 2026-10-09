import json

from dep_watch_agent.manifests import Declared, ManifestFile, declared, detect, is_manifest

PARENT_POM = """<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <version>1.4.0</version>
  <properties>
    <kafka.version>3.9.1</kafka.version>
    <spark.version>${spark.base}.1</spark.version>
    <spark.base>3.5</spark.base>
  </properties>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.apache.kafka</groupId>
        <artifactId>kafka-streams</artifactId>
        <version>${kafka.version}</version>
      </dependency>
    </dependencies>
  </dependencyManagement>
</project>
"""

CHILD_POM = """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <dependencies>
    <dependency>
      <groupId>org.apache.kafka</groupId>
      <artifactId>kafka-clients</artifactId>
      <version>${kafka.version}</version>
    </dependency>
    <dependency>
      <groupId>org.apache.kafka</groupId>
      <artifactId>kafka-streams</artifactId>
    </dependency>
    <dependency>
      <groupId>org.apache.spark</groupId>
      <artifactId>spark-core_2.13</artifactId>
      <version>${spark.version}</version>
    </dependency>
    <dependency>
      <groupId>com.example</groupId>
      <artifactId>internal</artifactId>
      <version>${project.version}</version>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>${undefined.version}</version>
    </dependency>
  </dependencies>
</project>
"""


def f(path: str, content: str) -> ManifestFile:
    return ManifestFile(path, content)


def versions(found: list[Declared]) -> dict[str, str | None]:
    return {d.coordinate: d.version for d in found}


def test_maven_resolves_properties_across_poms():
    found = declared([f("pom.xml", PARENT_POM), f("app/pom.xml", CHILD_POM)])
    assert versions(found) == {
        "org.apache.kafka:kafka-streams": "3.9.1",  # from the parent's dependencyManagement
        "org.apache.kafka:kafka-clients": "3.9.1",
        "org.apache.spark:spark-core_2.13": "3.5.1",  # a property built from a property
        "com.example:internal": "1.4.0",
        "org.slf4j:slf4j-api": None,  # unresolvable: listed without a guessed version
    }


def test_jvm_ranges_and_dynamic_versions_are_not_versions():
    pom = """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <properties><zk.range>[3.8,3.9)</zk.range></properties>
  <dependencies>
    <dependency>
      <groupId>org.apache.parquet</groupId><artifactId>parquet-avro</artifactId>
      <version>[1.13,1.15)</version>
    </dependency>
    <dependency>
      <groupId>org.apache.kafka</groupId><artifactId>kafka-clients</artifactId>
      <version>[3.9.1]</version>
    </dependency>
    <dependency>
      <groupId>org.apache.zookeeper</groupId><artifactId>zookeeper</artifactId>
      <version>${zk.range}</version>
    </dependency>
    <dependency>
      <groupId>org.apache.avro</groupId><artifactId>avro</artifactId>
      <version>LATEST</version>
    </dependency>
  </dependencies>
</project>
"""
    gradle = """
dependencies {
    implementation 'org.apache.hbase:hbase-client:2.5.+'
    implementation "org.apache.hive:hive-jdbc:latest.release"
    implementation group: 'org.apache.flink', name: 'flink-core', version: '[1.19,2.0)'
}
"""
    catalog = """
[versions]
spark = { require = "[3.5,4.0[", prefer = "3.5.3" }
cassandra = { require = "[4.1,5.0)" }

[libraries]
spark-sql = { module = "org.apache.spark:spark-sql_2.13", version.ref = "spark" }
cassandra-all = { module = "org.apache.cassandra:cassandra-all", version.ref = "cassandra" }
hadoop-client = "org.apache.hadoop:hadoop-client:3.+"
"""
    sbt = '"org.apache.iceberg" %% "iceberg-core" % "[1.5,1.7)"\n'
    found = declared(
        [
            f("pom.xml", pom),
            f("build.gradle", gradle),
            f("gradle/libs.versions.toml", catalog),
            f("build.sbt", sbt),
        ]
    )
    assert versions(found) == {
        "org.apache.parquet:parquet-avro": None,
        "org.apache.kafka:kafka-clients": "3.9.1",  # Maven's [x] is exactly x
        "org.apache.zookeeper:zookeeper": None,  # a range behind a property
        "org.apache.avro:avro": None,
        "org.apache.hbase:hbase-client": None,
        "org.apache.hive:hive-jdbc": None,
        "org.apache.flink:flink-core": None,
        "org.apache.spark:spark-sql_2.13": "3.5.3",  # the release the range prefers
        "org.apache.cassandra:cassandra-all": None,
        "org.apache.hadoop:hadoop-client": None,
        "org.apache.iceberg:iceberg-core": None,
    }


def test_a_lockfile_version_replaces_a_jvm_range():
    pom = """<project><dependencies><dependency>
  <groupId>org.apache.hbase</groupId><artifactId>hbase-client</artifactId>
  <version>[2.5,2.6)</version>
</dependency></dependencies></project>"""
    lockfile = "org.apache.hbase:hbase-client:2.5.10=runtimeClasspath\n"
    detected = detect([f("pom.xml", pom), f("gradle.lockfile", lockfile)])
    assert [(d.key, d.version) for d in detected] == [("hbase", "2.5.10")]


def test_gradle_build_files_with_variables_and_properties():
    groovy = """
ext.sparkVersion = '3.5.1'
dependencies {
    implementation "org.apache.kafka:kafka-clients:$kafkaVersion"
    implementation 'org.apache.spark:spark-sql_2.13:' + sparkVersion
    implementation group: 'org.apache.avro', name: 'avro', version: '1.11.3'
    testImplementation 'junit:junit:4.13.2'
}
"""
    kotlin = """
val flinkVersion = "1.19.1"
dependencies {
    implementation("org.apache.flink:flink-streaming-java:${flinkVersion}")
    implementation("org.apache.kafka:kafka-streams:${kafkaVersion}")
}
"""
    found = declared(
        [
            f("gradle.properties", "kafkaVersion=3.9.1\n# comment=1\n"),
            f("build.gradle", groovy),
            f("streams/build.gradle.kts", kotlin),
        ]
    )
    assert versions(found) == {
        "org.apache.kafka:kafka-clients": "3.9.1",
        "org.apache.avro:avro": "1.11.3",
        "junit:junit": "4.13.2",
        "org.apache.flink:flink-streaming-java": "1.19.1",
        "org.apache.kafka:kafka-streams": "3.9.1",
    }


def test_gradle_lockfile_and_version_catalog():
    lockfile = """# This is a Gradle generated file
org.apache.kafka:kafka-clients:3.9.1=compileClasspath,runtimeClasspath
org.lz4:lz4-java:1.8.0=runtimeClasspath
empty=annotationProcessor
"""
    catalog = """
[versions]
kafka = "3.9.1"
spark = { strictly = "3.5.1" }

[libraries]
kafka-clients = { module = "org.apache.kafka:kafka-clients", version.ref = "kafka" }
spark-core = { group = "org.apache.spark", name = "spark-core_2.13", version.ref = "spark" }
guava = "com.google.guava:guava:33.2.1-jre"
"""
    found = declared([f("gradle.lockfile", lockfile), f("gradle/libs.versions.toml", catalog)])
    assert versions(found) == {
        "org.apache.kafka:kafka-clients": "3.9.1",
        "org.lz4:lz4-java": "1.8.0",
        "org.apache.spark:spark-core_2.13": "3.5.1",
        "com.google.guava:guava": "33.2.1-jre",
    }


def test_sbt_sbom_and_compose():
    sbt = """
val sparkVersion = "3.5.1"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % sparkVersion % Provided,
  "org.apache.kafka" % "kafka-clients" % "3.9.1"
)
"""
    sbom = json.dumps(
        {
            "bomFormat": "CycloneDX",
            "components": [
                {"group": "org.apache.kafka", "name": "kafka-streams", "version": "3.9.1"},
                {"name": "no-group"},
            ],
        }
    )
    compose = """
services:
  broker:
    image: apache/kafka:3.9.1
  legacy:
    image: "docker.io/bitnami/kafka:3.7.0-debian-12-r0"
  db:
    image: postgres:16
"""
    found = declared([f("build.sbt", sbt), f("bom.json", sbom), f("docker-compose.yml", compose)])
    assert versions(found) == {
        "org.apache.spark:spark-sql": "3.5.1",
        "org.apache.kafka:kafka-clients": "3.9.1",
        "org.apache.kafka:kafka-streams": "3.9.1",
        "image:apache/kafka": "3.9.1",
        "image:bitnami/kafka": "3.7.0",  # the release, not the image build tag
        "image:postgres": "16",
    }


def test_detect_groups_by_family_and_version():
    files = [
        f("pom.xml", PARENT_POM),
        f("app/pom.xml", CHILD_POM),
        f("docker-compose.yml", "services:\n  b:\n    image: apache/kafka:3.9.1\n"),
    ]
    detected = {(d.key, d.version): d for d in detect(files)}

    kafka = detected[("kafka", "3.9.1")]
    assert kafka.name == "Apache Kafka"
    assert kafka.watchable and kafka.reason is None
    assert kafka.artifacts == [
        "org.apache.kafka:kafka-streams",
        "org.apache.kafka:kafka-clients",
        "image:apache/kafka",
    ]
    assert kafka.files == ["pom.xml", "app/pom.xml", "docker-compose.yml"]

    spark = detected[("spark", "3.5.1")]
    assert (spark.name, spark.watchable, spark.reason) == ("Apache Spark", True, None)

    unknown = detected[("org.slf4j:slf4j-api", None)]
    assert (unknown.family, unknown.watchable) == (None, False)

    # Watchable first, then known families, then the rest.
    hadoop = f("build.sbt", '"org.apache.hadoop" % "hadoop-aws" % "3.4.1"\n')
    assert [d.key for d in detect([*files, hadoop])][:3] == ["kafka", "spark", "hadoop"]


def test_a_watched_family_needs_a_release_version():
    pom = CHILD_POM.replace("${kafka.version}", "7.7.1-ccs", 1)
    detected = {(d.key, d.version): d for d in detect([f("pom.xml", pom)])}
    ccs = detected[("kafka", "7.7.1-ccs")]
    assert not ccs.watchable
    assert "is not a recognized release" in ccs.reason
    missing = detected[("kafka", None)]  # kafka-streams, whose version is managed elsewhere
    assert missing.reason == "Version not found in the manifests"


def test_broken_files_are_skipped():
    files = [f("pom.xml", "<project><unclosed>"), f("gradle.lockfile", "a:b:1.0=x\n")]
    assert versions(declared(files)) == {"a:b": "1.0"}


def test_is_manifest():
    for path in [
        "pom.xml",
        "svc/build.gradle.kts",
        "gradle/libs.versions.toml",
        "deploy/docker-compose.prod.yml",
        "compose.yaml",
        "target/app.cdx.json",
        "requirements-dev.txt",
        "pyproject.toml",
        "uv.lock",
        "web/package.json",
        "Dockerfile",
        "docker/api.Dockerfile",
    ]:
        assert is_manifest(path), path
    for path in ["README.md", "src/Main.java", "config.yml", "tsconfig.json", "setup.py"]:
        assert not is_manifest(path), path


def test_python_requirements_pyproject_and_locks():
    requirements = """# pinned
confluent-kafka==2.13.0
langchain_core==1.2.17  # inline comment
PySpark[sql]==3.5.1
requests>=2.31
-r other.txt
--hash=sha256:abc
git+https://github.com/x/y.git
"""
    pyproject = """
[project]
dependencies = ["fastapi>=0.110", "sqlalchemy==2.0.46"]
[project.optional-dependencies]
spark = ["apache-flink==1.19.1"]
[dependency-groups]
dev = ["pytest>=8"]
[tool.poetry.dependencies]
python = "^3.12"
httpx = "0.28.1"
pydantic = "^2.0"
"""
    uv_lock = """
[[package]]
name = "dep-watch-agent"
version = "0.1.0"
source = { editable = "." }

[[package]]
name = "FastAPI"
version = "0.141.1"
"""
    found = declared(
        [
            f("requirements.txt", requirements),
            f("pyproject.toml", pyproject),
            f("uv.lock", uv_lock),
        ]
    )
    assert versions(found) == {
        "pypi:confluent-kafka": "2.13.0",
        "pypi:langchain-core": "1.2.17",  # names normalized per PEP 503
        "pypi:pyspark": "3.5.1",
        "pypi:requests": None,  # a range is not a version
        "pypi:fastapi": "0.141.1",  # pyproject's range, then the lock's exact version
        "pypi:sqlalchemy": "2.0.46",
        "pypi:apache-flink": "1.19.1",
        "pypi:pytest": None,
        "pypi:httpx": "0.28.1",  # Poetry reads a bare version as exact
        "pypi:pydantic": None,
    }  # the project itself (editable) is not a dependency


def test_lockfile_versions_replace_ranges_and_families_cover_python():
    detected = {
        (d.key, d.version): d
        for d in detect(
            [
                f(
                    "pyproject.toml",
                    '[project]\ndependencies = ["fastapi>=0.110", "pyspark==3.5.1"]',
                ),
                f("uv.lock", '[[package]]\nname = "fastapi"\nversion = "0.141.1"\n'),
            ]
        )
    }
    assert ("pypi:fastapi", None) not in detected  # the lock gives the version
    fastapi = detected[("pypi:fastapi", "0.141.1")]
    assert (fastapi.name, fastapi.ecosystems, fastapi.files) == ("fastapi", ["pypi"], ["uv.lock"])
    spark = detected[("spark", "3.5.1")]
    assert (spark.name, spark.ecosystems) == ("Apache Spark", ["pypi"])


def test_a_dependency_lists_every_ecosystem_that_declares_it():
    compose = "services:\n  kafka:\n    image: apache/kafka:3.9.1\n"
    lockfile = "org.apache.kafka:kafka-clients:3.9.1=runtimeClasspath\n"
    detected = detect(
        [
            f("docker-compose.yml", compose),  # read first, listed after Maven
            f("gradle.lockfile", lockfile),
            f("requirements.txt", "pyspark==3.5.3\n"),
            f("build.sbt", '"org.apache.spark" %% "spark-sql" % "3.5.3"\n'),
        ]
    )
    assert {(d.key, d.version): d.ecosystems for d in detected} == {
        ("kafka", "3.9.1"): ["maven", "image"],
        ("spark", "3.5.3"): ["maven", "pypi"],
    }


def test_npm_package_json_with_lock():
    package = json.dumps(
        {
            "dependencies": {"react": "^18.3.1", "left-pad": "1.3.0"},
            "devDependencies": {"vite": "^5.4.11"},
        }
    )
    lock = json.dumps(
        {
            "packages": {
                "": {"dependencies": {"react": "^18.3.1"}, "devDependencies": {"vite": "^5.4.11"}},
                "node_modules/react": {"version": "18.3.1"},
                "node_modules/vite": {"version": "5.4.11"},
                "node_modules/rollup": {"version": "4.0.0"},  # transitive: left out
            }
        }
    )
    found = declared([f("web/package.json", package), f("web/package-lock.json", lock)])
    by_file = {(d.coordinate, d.version, d.file) for d in found}
    assert ("npm:left-pad", "1.3.0", "web/package.json") in by_file
    assert ("npm:react", None, "web/package.json") in by_file
    assert ("npm:react", "18.3.1", "web/package-lock.json") in by_file
    assert not any(d.artifact == "rollup" for d in found)


def test_images_from_compose_and_dockerfiles():
    compose = """
services:
  kafka:
    image: confluentinc/cp-kafka:7.4.0
  later:
    image: confluentinc/cp-server:7.4.3
  db:
    image: ankane/pgvector:latest   # comment
  ui:
    image: ${REGISTRY}/ui:1.0
  pinned:
    image: redis@sha256:abc
"""
    dockerfile = """
FROM --platform=linux/amd64 python:3.12-slim AS build
FROM build AS test
FROM node:20-alpine
FROM scratch
"""
    detected = {
        (d.key, d.version): d
        for d in detect([f("docker-compose.yaml", compose), f("Dockerfile", dockerfile)])
    }
    kafka = detected[("kafka", "3.4.0")]
    assert kafka.watchable
    assert kafka.notes == ["Confluent Platform 7.4.0 ships Apache Kafka 3.4.0"]
    # A later CP patch doesn't map one to one: no version is guessed.
    later = detected[("kafka", None)]
    assert not later.watchable
    assert later.notes == [
        "Confluent Platform 7.4.3 (Apache Kafka 3.4): add the exact Kafka version by hand"
    ]
    assert ("image:ankane/pgvector", "latest") in detected
    assert ("image:python", "3.12-slim") in detected
    assert ("image:node", "20-alpine") in detected
    assert ("image:redis", "latest") in detected  # a digest is not a version
    assert not any(k.startswith("image:${") or k == "image:build" for k, _ in detected)
