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
        "image:apache/kafka:apache/kafka": "3.9.1",
        "image:bitnami/kafka:bitnami/kafka": "3.7.0",  # the release, not the image build tag
    }  # postgres isn't a known dependency's image


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
        "image:apache/kafka:apache/kafka",
    ]
    assert kafka.files == ["pom.xml", "app/pom.xml", "docker-compose.yml"]

    spark = detected[("spark", "3.5.1")]
    assert (spark.name, spark.watchable, spark.reason) == ("Apache Spark", False, "Not watched yet")

    unknown = detected[("org.slf4j:slf4j-api", None)]
    assert (unknown.family, unknown.watchable) == (None, False)

    # Watchable first, then known families, then the rest.
    assert [d.key for d in detect(files)][:2] == ["kafka", "spark"]


def test_a_watched_family_needs_a_release_version():
    pom = CHILD_POM.replace("${kafka.version}", "7.7.1-ccs", 1)
    detected = {(d.key, d.version): d for d in detect([f("pom.xml", pom)])}
    ccs = detected[("kafka", "7.7.1-ccs")]
    assert not ccs.watchable
    assert "isn't a release" in ccs.reason
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
    ]:
        assert is_manifest(path), path
    for path in ["README.md", "src/Main.java", "config.yml", "package.json"]:
        assert not is_manifest(path), path
