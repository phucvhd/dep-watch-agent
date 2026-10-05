"""Find the dependencies a repository declares, and their versions, from its manifest files.

The browser reads the repository and sends only the manifests' text (``path`` is a label, never
opened here). Supported:

- JVM: Maven ``pom.xml`` (``${property}`` and ``<dependencyManagement>`` resolved across the
  poms sent), Gradle (``gradle.lockfile``, ``build.gradle[.kts]`` with ``gradle.properties``,
  ``libs.versions.toml``), sbt ``build.sbt``;
- Python: ``requirements*.txt``, ``pyproject.toml`` (PEP 621, PEP 735 groups, Poetry),
  ``uv.lock``, ``poetry.lock``, ``Pipfile.lock``;
- npm: ``package.json``, with exact versions from ``package-lock.json``;
- CycloneDX SBOMs; container images in Compose files and Dockerfiles. Confluent Platform's
  Kafka images are read as the Apache Kafka release they bundle, where that is exact.

A version that can't be resolved is reported as ``None`` rather than guessed (a range such as
``>=2.0`` or ``^18.3.1`` is not a version); the dependency is still listed, and a lockfile's
exact version replaces it when one is sent. Versions are strings as declared; whether one is a
release is decided by the family's version scheme, and nothing here compares versions.
"""

import json
import re
import tomllib
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from dep_watch_agent.dependencies import Family, family_for, family_for_image


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

    group: str  # a Maven group id, or the ecosystem: "pypi", "npm", "image"
    artifact: str
    version: str | None  # None when the declared version couldn't be resolved
    file: str
    note: str | None = None  # how the version was read, when not as written

    @property
    def coordinate(self) -> str:
        return f"{self.group}:{self.artifact}"

    @property
    def ecosystem(self) -> str:
        return self.group if self.group in ECOSYSTEMS else "maven"


ECOSYSTEMS = ("pypi", "npm", "image")


@dataclass(frozen=True)
class Detected:
    """A dependency at one version, across every file and artifact that declares it."""

    key: str  # a family id, or the coordinate for dependencies outside a known family
    name: str
    version: str | None
    family: str | None
    ecosystem: str  # maven, pypi, npm or image
    watchable: bool
    reason: str | None  # why it can't be watched, if it can't
    artifacts: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def is_manifest(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return (
        name in MANIFEST_NAMES
        or name.endswith((".cdx.json", ".gradle", ".gradle.kts", ".dockerfile"))
        or (name.startswith(("docker-compose", "compose")) and name.endswith((".yml", ".yaml")))
        or (name.startswith("requirements") and name.endswith(".txt"))
        or name.startswith("dockerfile")
    )


MANIFEST_NAMES = {
    "pom.xml",
    "gradle.lockfile",
    "gradle.properties",
    "libs.versions.toml",
    "build.sbt",
    "bom.json",
    "sbom.json",
    "pyproject.toml",
    "uv.lock",
    "poetry.lock",
    "pipfile.lock",
    "package.json",
    "package-lock.json",
}


def detect(files: Iterable[ManifestFile]) -> list[Detected]:
    """Every dependency declared, grouped by family (or coordinate) and version. Watchable
    ones first, then known families, then the rest; by name within each."""
    found = declared(list(files))
    # An artifact declared without a version in one file (a range, a managed version) and with
    # one in another (a lockfile) is listed at that version only.
    versioned = {d.coordinate for d in found if d.version is not None}
    groups: dict[tuple[str, str | None], Detected] = {}
    for d in found:
        if d.version is None and d.coordinate in versioned:
            continue
        family = family_for(d.group, d.artifact)
        key = family.id if family else d.coordinate
        entry = groups.get((key, d.version))
        if entry is None:
            watchable, reason = _watchability(family, d.version)
            entry = Detected(
                key=key,
                name=family.name if family else _plain_name(d),
                version=d.version,
                family=family.id if family else None,
                ecosystem=d.ecosystem,
                watchable=watchable,
                reason=reason,
            )
            groups[(key, d.version)] = entry
        if d.coordinate not in entry.artifacts:
            entry.artifacts.append(d.coordinate)
        if d.file not in entry.files:
            entry.files.append(d.file)
        if d.note and d.note not in entry.notes:
            entry.notes.append(d.note)
    return sorted(
        groups.values(),
        key=lambda e: (not e.watchable, e.family is None, e.name.lower(), e.version or ""),
    )


def _plain_name(d: Declared) -> str:
    return d.coordinate if d.ecosystem == "maven" else d.artifact


def _watchability(family: Family | None, version: str | None) -> tuple[bool, str | None]:
    if family is None or not family.watchable:
        return False, "Not watched yet"
    if version is None:
        return False, "Version not found in the manifests"
    if not family.scheme.is_release(version):
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
            elif name.startswith("dockerfile") or name.endswith(".dockerfile"):
                found += _dockerfile(f)
            elif name.startswith("requirements") and name.endswith(".txt"):
                found += _requirements(f)
            elif name == "pyproject.toml":
                found += _pyproject(f)
            elif name in ("uv.lock", "poetry.lock"):
                found += _python_lock(f)
            elif name == "pipfile.lock":
                found += _pipfile_lock(f)
            elif name == "package.json":
                found += _package_json(f)
            elif name == "package-lock.json":
                found += _package_lock(f)
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


_COMPOSE_IMAGE = re.compile(r"""^\s*image:\s*["']?([^\s"'#]+)["']?\s*(?:#.*)?$""", re.M)
_FROM = re.compile(r"^\s*FROM\s+(?:--\S+\s+)*(\S+)(?:\s+AS\s+(\S+))?", re.M | re.I)
_LEADING_VERSION = re.compile(r"^v?(\d+(?:\.\d+){1,3})")

# Confluent Platform x.y.0 ships Apache Kafka a.b.0: its Kafka images stand for that release.
# Later CP patches don't map one to one onto Kafka patches, so those are left for the user.
CONFLUENT_KAFKA_IMAGES = ("confluentinc/cp-kafka", "confluentinc/cp-server")
CONFLUENT_TO_KAFKA_LINE = {
    (5, 0): (2, 0), (5, 1): (2, 1), (5, 2): (2, 2), (5, 3): (2, 3), (5, 4): (2, 4),
    (5, 5): (2, 5), (6, 0): (2, 6), (6, 1): (2, 7), (6, 2): (2, 8), (7, 0): (3, 0),
    (7, 1): (3, 1), (7, 2): (3, 2), (7, 3): (3, 3), (7, 4): (3, 4), (7, 5): (3, 5),
    (7, 6): (3, 6), (7, 7): (3, 7), (7, 8): (3, 8), (7, 9): (3, 9), (8, 0): (4, 0),
}  # fmt: skip


def _image(reference: str, file: str) -> Declared | None:
    """``registry/name:tag`` as a dependency on the image ``name`` at ``tag``."""
    if "$" in reference or reference == "scratch":
        return None
    reference = reference.split("@", 1)[0]  # a digest pins bytes, not a version
    name, _, tag = (
        reference.rpartition(":") if ":" in reference.split("/")[-1] else (reference, "", "")
    )
    name = name.removeprefix("docker.io/").removeprefix("library/")
    if name in CONFLUENT_KAFKA_IMAGES:
        return _confluent_kafka(name, tag, file)
    if family_for_image(name):
        match = _LEADING_VERSION.match(tag)  # bitnami tags look like 3.9.1-debian-12-r0
        return Declared("image", name, match.group(1) if match else None, file)
    return Declared("image", name, tag or "latest", file)


def _confluent_kafka(name: str, tag: str, file: str) -> Declared:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", tag)
    line = CONFLUENT_TO_KAFKA_LINE.get((int(match[1]), int(match[2]))) if match else None
    if match and line and match[3] == "0":
        kafka = f"{line[0]}.{line[1]}.0"
        return Declared(
            "image", name, kafka, file, note=f"Confluent Platform {tag} ships Apache Kafka {kafka}"
        )
    hint = f" (Apache Kafka {line[0]}.{line[1]})" if line else ""
    return Declared(
        "image",
        name,
        None,
        file,
        note=f"Confluent Platform {tag or 'latest'}{hint}: add the exact Kafka version by hand",
    )


def _compose(f: ManifestFile) -> list[Declared]:
    images = (_image(reference, f.path) for reference in _COMPOSE_IMAGE.findall(f.content))
    return [d for d in images if d]


def _dockerfile(f: ManifestFile) -> list[Declared]:
    stages: set[str] = set()
    found = []
    for reference, stage in _FROM.findall(f.content):
        if reference.lower() not in stages:  # FROM an earlier stage is not an image
            d = _image(reference, f.path)
            if d:
                found.append(d)
        if stage:
            stages.add(stage.lower())
    return found


# --- Python ------------------------------------------------------------------------------

_REQUIREMENT = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:(===?)\s*([^\s,;#]+))?"
)
_EXACT_VERSION = re.compile(r"^\d+(?:\.\d+)*(?:[-.]?[A-Za-z]+\d*)?$")


def pypi_name(name: str) -> str:
    """PEP 503: names are compared lowercase with runs of -, _ and . as one -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement(spec: str, file: str) -> Declared | None:
    """A PEP 508 requirement; only ``==`` pins a version."""
    match = _REQUIREMENT.match(spec)
    if not match:
        return None
    version = match[3] if match[2] and "*" not in (match[3] or "") else None
    return Declared("pypi", pypi_name(match[1]), version, file)


def _requirements(f: ManifestFile) -> list[Declared]:
    found = []
    for line in f.content.splitlines():
        line = line.split(" #", 1)[0].strip()
        if not line or line.startswith(("#", "-", "git+", "http:", "https:", "file:", ".")):
            continue  # comments, options (-r, -e, --hash), and direct references
        d = _requirement(line, f.path)
        if d:
            found.append(d)
    return found


def _pyproject(f: ManifestFile) -> list[Declared]:
    data = tomllib.loads(f.content)
    project = data.get("project", {})
    specs = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs += group
    for group in data.get("dependency-groups", {}).values():
        specs += [s for s in group if isinstance(s, str)]
    found = [d for s in specs if (d := _requirement(s, f.path))]

    poetry = data.get("tool", {}).get("poetry", {})
    tables = [poetry.get("dependencies", {}), poetry.get("dev-dependencies", {})]
    tables += [g.get("dependencies", {}) for g in poetry.get("group", {}).values()]
    for table in tables:
        for name, value in table.items():
            if name.lower() == "python":
                continue
            version = value.get("version") if isinstance(value, dict) else value
            # Poetry reads a bare version as exact; ^, ~ and ranges are not a version.
            exact = isinstance(version, str) and _EXACT_VERSION.match(version.removeprefix("=="))
            found.append(
                Declared(
                    "pypi", pypi_name(name), version.removeprefix("==") if exact else None, f.path
                )
            )
    return found


def _python_lock(f: ManifestFile) -> list[Declared]:
    found = []
    for package in tomllib.loads(f.content).get("package", []):
        source = package.get("source", {})
        if "editable" in source or "virtual" in source:
            continue  # the project itself, not a dependency
        if package.get("name") and package.get("version"):
            found.append(Declared("pypi", pypi_name(package["name"]), package["version"], f.path))
    return found


def _pipfile_lock(f: ManifestFile) -> list[Declared]:
    lock = json.loads(f.content)
    found = []
    for section in ("default", "develop"):
        for name, entry in (lock.get(section) or {}).items():
            version = entry.get("version", "") if isinstance(entry, dict) else ""
            found.append(
                Declared("pypi", pypi_name(name), version.removeprefix("==") or None, f.path)
            )
    return found


# --- npm ---------------------------------------------------------------------------------

_NPM_SECTIONS = ("dependencies", "devDependencies", "optionalDependencies")


def _package_json(f: ManifestFile) -> list[Declared]:
    manifest = json.loads(f.content)
    found = []
    for section in _NPM_SECTIONS:
        for name, spec in (manifest.get(section) or {}).items():
            exact = isinstance(spec, str) and re.fullmatch(r"\d+\.\d+\.\d+(?:-[\w.]+)?", spec)
            found.append(Declared("npm", name, spec if exact else None, f.path))
    return found


def _package_lock(f: ManifestFile) -> list[Declared]:
    """Exact versions of the root package's direct dependencies; transitive ones are left out
    (a lock lists hundreds)."""
    lock = json.loads(f.content)
    packages = lock.get("packages") or {}
    root = packages.get("", {})
    direct = {name for section in _NPM_SECTIONS for name in (root.get(section) or {})}
    found = []
    for name in sorted(direct):
        version = (packages.get(f"node_modules/{name}") or {}).get("version")
        if version:
            found.append(Declared("npm", name, version, f.path))
    return found
