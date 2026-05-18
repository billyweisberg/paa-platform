"""Models for the acceptance policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AcceptanceRequest:
    work_item_id: str
    workflow_stage: str | None
    result_schema_type: str | None = None
    verification_status: str | None = None
    merge_ready: bool | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class AcceptanceEvaluationContext:
    current_workflow_stage: str | None
    has_blocking_findings: bool = False
    protected_path_checks_passed: bool | None = None
    approved_contract_change: bool | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class AcceptanceDecision:
    accepted: bool
    terminal: bool
    acceptance_code: str | None
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any]


__all__ = [
    'AcceptanceDecision',
    'AcceptanceEvaluationContext',
    'AcceptanceRequest',
]
