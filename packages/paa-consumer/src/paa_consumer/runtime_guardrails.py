"""Consumer-facing guardrail entrypoints."""

from __future__ import annotations

from pathlib import Path

from paa_core.runtime_guardrails import validate_consumer_runtime


def validate(repo_root: Path) -> dict[str, object]:
    return validate_consumer_runtime(repo_root)
