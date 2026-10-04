"""The dependencies the system watches. Only Apache Kafka for now (see CLAUDE.md, out of scope:
other dependencies); the API lists them so clients don't hard-code the choice."""

from dataclasses import dataclass


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
