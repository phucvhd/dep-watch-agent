"""The systems that can answer checks and be scored by the eval, by name.

A system is a factory for an extractor (``eval.runner.Extractor``): it turns issue text into
cited version facts, and ``verdict.decide`` makes the decision. Systems are compared with each
other on the same metrics; there is no fixed baseline. ``POST /check`` uses the first one
registered.
"""

from collections.abc import Callable

from dep_watch_agent.eval.runner import Extractor

SystemRegistry = dict[str, Callable[[], Extractor]]

SYSTEMS: SystemRegistry = {}
