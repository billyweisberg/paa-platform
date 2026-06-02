from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeOperationResult:
    payload: dict[str, Any]
    exit_code: int = 0


@dataclass(frozen=True)
class RuntimeSupervisorRequest:
    repo_root: Path
    intake_mode: str = 'claim_next'
    emit_next_assignment: bool = True
    emit_worker_result: bool = True
    emit_verification: bool = True
    max_iterations: int = 0
    poll_interval_seconds: float = 5.0


@dataclass(frozen=True)
class RuntimeStatusRequest:
    repo_root: Path


@dataclass(frozen=True)
class RuntimeLogsRequest:
    repo_root: Path
    lines: int = 200


@dataclass(frozen=True)
class RuntimeHostRunRequest:
    repo_root: Path
    actor_name: str
    host_name: str
    intake_mode: str = 'preview'
    max_iterations: int = 1
    poll_interval_seconds: float = 5.0
    emit_next_assignment: bool = False
    emit_worker_result: bool = False
    emit_verification: bool = False
