"""Rule-based baseline: regex extraction of version facts, no LLM.

This is the system every LLM change is measured against. For each mention of a known Kafka
release in the text, it looks at the words just before the mention (same line or sentence) and
classifies the mention by the nearest cue:

- fix cues: "fixed in", "merged to", "cherry-picked to", "backported to", "no longer happens in"
- affects cues: "affects", "since", "reproduced on", "upgraded to", "still present in", and
  artifact names in stack traces such as ``kafka-clients-2.4.0.jar``
- neutral cues ("from", "not", "works fine on") cancel the classification

Mentions with no cue are ignored. Each fact is cited with the line or sentence it came from, so
citations are valid by construction. The decision itself is made by ``verdict.decide``.

Known limits, by design: no understanding of negation beyond the neutral cues, no
cross-sentence reasoning, release lines ("3.7", "refs/heads/3.7") are ignored.
"""

import re

from dep_watch_agent.verdict import Evidence, EvidenceKind, Extraction, IssueText, is_release
from dep_watch_agent.versions import Version, VersionParseError, parse_version

_VERSION = re.compile(r"(?<![\w.])v?\d+\.\d+(?:\.\d+){0,2}(?:-rc\d+)?(?![\w.]*\d)")

# A mention is judged by the cues in this many characters before it, within its segment.
WINDOW = 60

_CUES: list[tuple[EvidenceKind | None, re.Pattern[str]]] = [
    (kind, re.compile(pattern, re.IGNORECASE))
    for kind, pattern in [
        # fix
        ("fix", r"\bfix(?:ed|es)?\b(?:\s+\w+){0,2}?\s+(?:in|on|for|by|into)\b"),
        ("fix", r"\bfix(?:ed)?\s+versions?\b\W*"),
        ("fix", r"\bresolved\s+(?:in|on|for)\b"),
        ("fix", r"\bmerged\b(?:\s+\w+){0,3}?\s+(?:to|into|in|on)\b"),
        ("fix", r"\bcherry[- ]?pick(?:ed|ing)?\b(?:\s+\w+){0,3}?\s+(?:to|into|on|onto)\b"),
        ("fix", r"\bback-?port(?:ed|ing|s)?\b(?:\s+\w+){0,3}?\s+(?:to|into|on)\b"),
        ("fix", r"\b(?:checked|committed|pushed|landed|included|shipped)\s+(?:in|into|to|on)\b"),
        ("fix", r"\bno\s+longer\s+(?:\w+\s+){0,3}?(?:in|on|with)\b"),
        # affects
        ("affects", r"\baffect(?:s|ed|ing)?\b(?:\s+versions?)?\W*"),
        ("affects", r"\bsince\b"),
        (
            "affects",
            r"\b(?:reproduc|observ|occur|happen|introduc)\w*\b(?:\s+\w+){0,2}?\s+(?:in|on|with)\b",
        ),
        ("affects", r"\b(?:see|seeing|seen|saw)\b(?:\s+\w+){0,3}?\s+(?:in|on|with)\b"),
        ("affects", r"\b(?:running|using|run)\b(?:\s+\w+){0,2}?\s+(?:on|with|kafka)?\b"),
        ("affects", r"\bupgrad\w*\b[^\n]{0,30}?\bto\b"),
        ("affects", r"\bmigrat\w*\s+to\b"),
        ("affects", r"\b(?:broken|regression|bug|issue|problem|fails?|failing)\s+(?:in|on|with)\b"),
        ("affects", r"\bstill\s+(?:\w+\s+){0,2}?(?:in|on|with)\b"),
        ("affects", r"\bkafka(?:[-_](?:clients|streams|connect|tools|server|\d+\.\d+))*[-_]$"),
        # neutral: cancels whatever cue came before it
        (None, r"\bfrom\b"),
        (None, r"(?:\bnot\b|\bnever\b|n't\b)(?:\s+\w+){0,2}?\s+(?:in|on|with)\b"),
        (None, r"\bworks?\s+(?:fine|well|ok|correctly)?\s*(?:in|on|with)\b"),
    ]
]

# A line or sentence. Punctuation followed by a word character (3.7.0, e.g., Foo.java) doesn't
# end it.
# Between a cue and its version only filler may appear: "fixed in 3.7.1 and 3.8.0",
# "running Apache Kafka 2.3.1". Anything else ("since it is not ready for 2.0.0") breaks the link.
_GAP = re.compile(
    r"(?:\s|[,/&()]|\b(?:and|or|the|apache|kafka|streams|connect|clients|version|versions|"
    r"release|releases|branch|v)\b|v?\d+(?:\.\d+)+)*",
    re.IGNORECASE,
)

_SEGMENT = re.compile(r"(?:[^\n.!?]|[.!?](?=\w))+[.!?]?")


class RuleBasedExtractor:
    name = "baseline-rules"

    def __init__(self, known_versions: set[Version]):
        self._known = known_versions

    def extract(self, issue: IssueText) -> Extraction:
        evidence: list[Evidence] = []
        seen: set[tuple[str, str]] = set()
        for text in issue.fields():
            for start, end in _segments(text):
                segment = text[start:end]
                for match in _VERSION.finditer(segment):
                    ev = self._classify(segment, match)
                    if ev and (ev.version, ev.kind) not in seen:
                        seen.add((ev.version, ev.kind))
                        evidence.append(ev)
        return Extraction(evidence)

    def _classify(self, segment: str, match: re.Match[str]) -> Evidence | None:
        raw = match.group()
        if not is_release(raw):
            return None
        try:
            if parse_version(raw) not in self._known:
                return None
        except VersionParseError:
            return None

        window = segment[max(0, match.start() - WINDOW) : match.start()]
        kind = _nearest_cue(window)
        if kind is None:
            return None
        return Evidence(version=raw.lstrip("vV"), kind=kind, quote=segment.strip())


def _nearest_cue(window: str) -> EvidenceKind | None:
    """Kind of the cue ending closest to the mention; longest match breaks ties. Only cues
    separated from the mention by filler count."""
    best: tuple[int, int, EvidenceKind | None] | None = None
    for kind, pattern in _CUES:
        for m in pattern.finditer(window):
            if not _GAP.fullmatch(window[m.end() :]):
                continue
            key = (m.end(), m.end() - m.start(), kind)
            if best is None or key[:2] > best[:2]:
                best = key
    return best[2] if best else None


def _segments(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _SEGMENT.finditer(text) if m.group().strip()]
