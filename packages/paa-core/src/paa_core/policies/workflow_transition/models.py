"""Models for the workflow transition policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowTransitionRequest:
    work_item_id: str
    transition_type: str
    requested_by_role: str | None = None
    requested_by_agent: str | None = None
    requested_from_stage: str | None = None
    requested_to_stage: str | None = None
    source_schema_type: str | None = None
    result_schema_type: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowTransitionEvaluationContext:
    current_workflow_stage: str | None
    current_owner_role: str | None
    lineage_state: str | None = None
    state_consistency: str | None = None
    execution_surface_type: str | None = None
    execution_surface_key: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowTransitionDecision:
    allowed: bool
    resolved_to_stage: str | None
    rejection_code: str | None
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any]


__all__ = [
    'WorkflowTransitionDecision',
    'WorkflowTransitionEvaluationContext',
    'WorkflowTransitionRequest',
]
