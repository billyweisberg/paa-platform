from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeValidationRequest:
    repo_root: Path
    expected_branch: str | None = None


@dataclass(frozen=True)
class RuntimeSmokeRequest:
    repo_root: Path
    expected_branch: str | None = None
    output_path: Path | None = None


@dataclass(frozen=True)
class RuntimeStatusResultView:
    payload: dict[str, Any]
    exit_code: int = 0


@dataclass(frozen=True)
class TechLeadServiceMapResultView:
    payload: dict[str, Any]
    exit_code: int = 0
