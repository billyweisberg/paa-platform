"""Project-local PAA config helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfigRef:
    """Pointer to a repo-local PAA project config file."""

    path: Path
    mode: str

