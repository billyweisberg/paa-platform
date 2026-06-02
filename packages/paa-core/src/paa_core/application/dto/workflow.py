from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AutomationPreflightRequest:
    repo_root: Path
    project_slug: str
    target_role: str


@dataclass(frozen=True)
class AutomationPreflightResultView:
    payload: dict[str, Any]
    exit_code: int = 0
