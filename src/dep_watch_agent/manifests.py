"""Find the dependencies a repository declares, and their versions, from its manifest files.

The browser reads the repository and sends only the manifests' text (``path`` is a label, never
opened here). Supported: Maven ``pom.xml`` (with ``${property}`` resolution across the poms
sent), Gradle (``gradle.lockfile``, ``build.gradle[.kts]`` with ``gradle.properties``,
``libs.versions.toml``), sbt ``build.sbt``, CycloneDX SBOMs, and container images in Compose
files.

A version that can't be resolved is reported as ``None`` rather than guessed; the dependency
is still listed. Versions are strings as declared; whether one is a release is decided by
``verdict.is_release``, and nothing here compares versions.
"""

import json
import re
import tomllib
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from dep_watch_agent.dependencies import Family, family_for_group, family_for_image
from dep_watch_agent.verdict import is_release


@dataclass(frozen=True)
class ManifestFile:
    path: str
    content: str

    @property
    def name(self) -> str:
        return PurePosixPath(self.path).name


@dataclass(frozen=True)
class Declared:
    """One dependency as one file declares it."""

    group: str
    artifact: str
    version: str | None  # None when the declared version couldn't be resolved
    file: str

    @property
    def coordinate(self) -> str:
        return f"{self.group}:{self.artifact}"


@dataclass(frozen=True)
class Detected:
    """A dependency at one version, across every file and artifact that declares it."""

    key: str  # a family id, or the coordinate for dependencies outside a known family
    name: str
    version: str | None
    family: str | None
    watchable: bool
    reason: str | None  # why it can't be watched, if it can't
    artifacts: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)


def is_manifest(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return (
        name in MANIFEST_NAMES
        or name.endswith((".cdx.json", ".gradle", ".gradle.kts"))
        or (name.startswith(("docker-compose", "compose")) and name.endswith((".yml", ".yaml")))
    )


MANIFEST_NAMES = {
    "pom.xml",
    "gradle.lockfile",
    "gradle.properties",
    "libs.versions.toml",
    "build.sbt",
    "bom.json",
    "sbom.json",
}


def detect(files: Iterable[ManifestFile]) -> list[Detected]:
    """Every dependency declared, grouped by family (or coordinate) and version. Watchable
    ones first, then known families, then the rest; by name within each."""
    files = list(files)
    groups: dict[tuple[str, str | None], Detected] = {}
    for d in declared(files):
        if d.group.startswith("image:"):
            family = family_for_image(d.group.removeprefix("image:"))
        else:
            family = family_for_group(d.group)
        key = family.id if family else d.coordinate
        entry = groups.get((key, d.version))
        if entry is None:
            watchable, reason = _watchability(family, d.version)
            entry = Detected(
                key=key,
                name=family.name if family else d.coordinate,
                version=d.version,
                family=family.id if family else None,
                watchable=watchable,
                reason=reason,
            )
            groups[(key, d.version)] = entry
        if d.coordinate not in entry.artifacts:
            entry.artifacts.append(d.coordinate)
        if d.file not in entry.files:
            entry.files.append(d.file)
    return sorted(
        groups.values(),
        key=lambda e: (not e.watchable, e.family is None, e.name.lower(), e.version or ""),
    )


def _watchability(family: Family | None, version: str | None) -> tuple[bool, str | None]:
    if family is None or not family.watchable:
        return False, "Not watched yet"
    if version is None:
        return False, "Version not found in the manifests"
    if not is_release(version):
        return False, f"{version} isn't a release this system knows"
    return True, None


def declared(files: list[ManifestFile]) -> list[Declared]:
    """Every dependency each file declares, with versions resolved where possible."""
    properties = _gradle_properties(files)
    pom_properties = _pom_properties(files)
    pom_managed = _pom_managed(files)
    found: list[Declared] = []
    for f in files:
        name = f.name.lower()
        try:
            if name == "pom.xml":
                found += _pom(f, pom_properties, pom_managed)
            elif name == "gradle.lockfile":
                found += _gradle_lockfile(f)
            elif name == "libs.versions.toml":
                found += _version_catalog(f)
            elif name.endswith((".gradle", ".gradle.kts")):
                found += _gradle_build(f, properties)
            elif name == "build.sbt":
                found += _sbt(f)
            elif name.endswith((".cdx.json",)) or name in ("bom.json", "sbom.json"):
                found += _cyclonedx(f)
            elif name.endswith((".yml", ".yaml")):
                found += _compose(f)
        except (ET.ParseError, tomllib.TOMLDecodeError, json.JSONDecodeError, ValueError):
            continue  # an unreadable file contributes nothing; the others still count
    return found


# --- Maven -------------------------------------------------------------------------------

_PROPERTY = re.compile(r"\$\{([^}]+)\}")


def _strip_namespaces(root: ET.Element) -> ET.Element:
    for element in root.iter():
        if isinstance(element.tag, str) and "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]
    return root


def _pom_root(f: ManifestFile) -> ET.Element:
    return _strip_namespaces(ET.fromstring(f.content))


def _pom_properties(files: list[ManifestFile]) -> dict[str, str]:
    """Properties from every pom sent, so a child's ``${kafka.version}`` resolves against a
    parent's ``<properties>``."""
    props: dict[str, str] = {}
    for f in files:
        if f.name.lower() != "pom.xml":
            continue
        try:
            root = _pom_root(f)
        except ET.ParseError:
            continue
        for p in root.findall("properties/*"):
            if isinstance(p.tag, str) and p.text:
                props.setdefault(p.tag, p.text.strip())
        for tag in ("version", "parent/version"):
            version = root.findtext(tag)
            if version:
                props.setdefault("project.version", version.strip())
    return props


def _pom_managed(files: list[ManifestFile]) -> dict[tuple[str, str], str]:
    """``<dependencyManagement>`` versions from every pom sent: a module often declares a
    dependency without a version and inherits it from the parent's management section."""
    managed: dict[tuple[str, str], str] = {}
    for f in files:
        if f.name.lower() != "pom.xml":
            continue
        try:
            root = _pom_root(f)
        except ET.ParseError:
            continue
        for d in root.findall("dependencyManagement/dependencies/dependency"):
            group, artifact, version = (
                d.findtext("groupId"),
                d.findtext("artifactId"),
                d.findtext("version"),
            )
            if group and artifact and version:
                managed.setdefault((group.strip(), artifact.strip()), version.strip())
    return managed


def _resolve(value: str | None, props: dict[str, str]) -> str | None:
    if value is None:
        return None
    for _ in range(5):  # properties may refer to properties
        value = _PROPERTY.sub(lambda m: props.get(m.group(1), m.group(0)), value)
    return None if _PROPERTY.search(value) else value.strip() or None


def _pom(
    f: ManifestFile, props: dict[str, str], managed: dict[tuple[str, str], str]
) -> list[Declared]:
    root = _pom_root(f)
    local = {**props, **{p.tag: (p.text or "").strip() for p in root.findall("properties/*")}}
    found = []
    for path in ("dependencies/dependency", "dependencyManagement/dependencies/dependency"):
        for d in root.findall(path):
            group, artifact = d.findtext("groupId"), d.findtext("artifactId")
            if not group or not artifact:
                continue
            version = d.findtext("version") or managed.get((group.strip(), artifact.strip()))
            found.append(
                Declared(group.strip(), artifact.strip(), _resolve(version, local), f.path)
            )
    return found


# --- Gradle ------------------------------------------------------------------------------

_GRADLE_COORD = re.compile(r"""["']([\w.\-]+):([\w.\-]+):([^"'@:\s]+)(?:@\w+)?["']""")
_GRADLE_MAP = re.compile(
    r"""group\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*name\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*"""
    r"""version\s*[:=]\s*["']([^"']+)["']"""
)
_GRADLE_ASSIGN = re.compile(
    r"""^\s*(?:val\s+|def\s+|ext\.|set\(\s*["'])?([\w.]+)["']?\s*[=,]\s*["']([^"'$]+)["']""",
    re.M,
)
_GRADLE_VAR = re.compile(r"\$\{?([\w.]+)\}?")


def _gradle_properties(files: list[ManifestFile]) -> dict[str, str]:
    props: dict[str, str] = {}
    for f in files:
        if f.name.lower() == "gradle.properties":
            for line in f.content.splitlines():
                key, sep, value = line.partition("=")
                if sep and not key.strip().startswith("#"):
                    props.setdefault(key.strip(), value.strip())
    return props


def _gradle_lockfile(f: ManifestFile) -> list[Declared]:
    found = []
    for line in f.content.splitlines():
        coordinate = line.split("=", 1)[0].strip()
        parts = coordinate.split(":")
        if len(parts) == 3 and not line.startswith("#"):
            found.append(Declared(parts[0], parts[1], parts[2], f.path))
    return found


def _gradle_build(f: ManifestFile, props: dict[str, str]) -> list[Declared]:
    variables = {**props, **dict(_GRADLE_ASSIGN.findall(f.content))}

    def resolve(version: str) -> str | None:
        if "$" not in version:
            return version
        resolved = _GRADLE_VAR.sub(lambda m: variables.get(m.group(1), m.group(0)), version)
        return None if "$" in resolved else resolved

    found = []
    for group, artifact, version in _GRADLE_COORD.findall(f.content) + _GRADLE_MAP.findall(
        f.content
    ):
        found.append(Declared(group, artifact, resolve(version), f.path))
    return found


def _version_catalog(f: ManifestFile) -> list[Declared]:
    catalog = tomllib.loads(f.content)
    versions = catalog.get("versions", {})

    def version_of(value) -> str | None:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):  # {strictly = "..."} / {require = "..."} / {prefer = "..."}
            return next((value[k] for k in ("strictly", "require", "prefer") if k in value), None)
        return None

    found = []
    for entry in catalog.get("libraries", {}).values():
        if isinstance(entry, str):
            parts = entry.split(":")
            if len(parts) == 3:
                found.append(Declared(parts[0], parts[1], parts[2], f.path))
            continue
        if "module" in entry:
            group, _, artifact = entry["module"].partition(":")
        else:
            group, artifact = entry.get("group", ""), entry.get("name", "")
        version = entry.get("version")
        if isinstance(version, dict) and "ref" in version:
            version = version_of(versions.get(version["ref"]))
        elif "version.ref" in entry:
            version = version_of(versions.get(entry["version.ref"]))
        else:
            version = version_of(version)
        if group and artifact:
            found.append(Declared(group, artifact, version, f.path))
    return found


# --- sbt, SBOM, Compose ------------------------------------------------------------------

_SBT_DEP = re.compile(r""""([\w.\-]+)"\s*%{1,3}\s*"([\w.\-]+)"\s*%\s*(?:"([^"]+)"|(\w+))""")
_SBT_VAL = re.compile(r"""\bval\s+(\w+)\s*=\s*"([^"]+)\"""")


def _sbt(f: ManifestFile) -> list[Declared]:
    values = dict(_SBT_VAL.findall(f.content))
    return [
        Declared(group, artifact, literal or values.get(name), f.path)
        for group, artifact, literal, name in _SBT_DEP.findall(f.content)
    ]


def _cyclonedx(f: ManifestFile) -> list[Declared]:
    bom = json.loads(f.content)
    found = []
    for c in bom.get("components", []) if isinstance(bom, dict) else []:
        if isinstance(c, dict) and c.get("group") and c.get("name"):
            found.append(Declared(c["group"], c["name"], c.get("version"), f.path))
    return found


_IMAGE = re.compile(r"""^\s*image:\s*["']?([\w./\-]+):([\w.\-]+)["']?\s*$""", re.M)
_LEADING_VERSION = re.compile(r"^v?(\d+(?:\.\d+){1,3})")


def _compose(f: ManifestFile) -> list[Declared]:
    found = []
    for image, tag in _IMAGE.findall(f.content):
        image = image.removeprefix("docker.io/")
        if family_for_image(image) is None:
            continue  # only images that stand for a known dependency
        match = _LEADING_VERSION.match(tag)  # bitnami tags look like 3.9.1-debian-12-r0
        found.append(Declared(f"image:{image}", image, match.group(1) if match else None, f.path))
    return found
