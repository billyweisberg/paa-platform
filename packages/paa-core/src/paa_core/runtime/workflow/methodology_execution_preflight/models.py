"""Models for the methodology execution preflight service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.runtime.workflow.methodology_execution_projection import MethodologyExecutionStatusProjection


@dataclass(frozen=True)
class MethodologyExecutionPreflightRequest:
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    command_family: str | None = None
    command_name: str | None = None
    command_arguments: dict[str, Any] | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionPreflightOutcome:
    methodology_execution_id: str | None
    outcome_kind: str
    rule_key: str | None
    lane: str | None
    stage: str | None
    step: str | None
    status: str | None
    current_owner_role: str | None
    redirect_target: str | None
    recommended_next_action_key: str | None
    reason: str
    details: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionPreflightResult:
    methodology_execution_id: str | None
    request: MethodologyExecutionPreflightRequest
    status_projection: MethodologyExecutionStatusProjection | None
    outcome: MethodologyExecutionPreflightOutcome
    ok: bool
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'MethodologyExecutionPreflightOutcome',
    'MethodologyExecutionPreflightRequest',
    'MethodologyExecutionPreflightResult',
]
