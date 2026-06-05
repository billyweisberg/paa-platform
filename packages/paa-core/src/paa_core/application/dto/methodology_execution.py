from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MethodologyExecutionOperationResult:
    payload: dict[str, Any]
    exit_code: int = 0


@dataclass(frozen=True)
class GetMethodologyExecutionStatusRequest:
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None


@dataclass(frozen=True)
class GetMethodologyExecutionNextActionRequest:
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None


@dataclass(frozen=True)
class ExplainMethodologyExecutionRequest:
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None


@dataclass(frozen=True)
class MethodologyExecutionBindingEntryInput:
    binding_kind: str
    bound_record_id: str | None = None
    bound_record_key: str | None = None
    bound_record_ref: str | None = None
    is_primary: bool = False
    notes: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ApplyMethodologyExecutionTransitionRequest:
    transition_key: str
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    notes: str | None = None
    evidence: dict[str, Any] | None = None
    binding_entries: tuple[MethodologyExecutionBindingEntryInput, ...] = ()
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class EvaluateMethodologyExecutionPreflightRequest:
    command_family: str
    command_name: str
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    command_arguments: dict[str, Any] | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    metadata: dict[str, Any] | None = None
