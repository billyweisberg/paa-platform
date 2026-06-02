"""Consumer-facing guardrail entrypoints."""

from __future__ import annotations

from pathlib import Path

from paa_core.runtime_guardrails import validate_runtime_install


def validate(repo_root: Path) -> dict[str, object]:
    return validate_runtime_install(repo_root)
