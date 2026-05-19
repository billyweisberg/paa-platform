"""Contracts for the workflow lifecycle service."""

from __future__ import annotations

from typing import Protocol

from paa_core.policies.acceptance import AcceptancePolicy
from paa_core.policies.reset_recovery import ResetRecoveryPolicy
from paa_core.policies.workflow_transition import WorkflowTransitionPolicy
from paa_core.repositories.runtime_event import RuntimeEventRepository
from paa_core.repositories.workflow_state import WorkflowStateRepository
from paa_core.services.execution_package_resolution import ExecutionPackageResolutionService
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    WorkflowLifecycleRequest,
    WorkflowLifecycleResult,
    WorkflowLifecycleStateView,
)


class WorkflowLifecycleService(Protocol):
    """Coordinate authoritative workflow transition evaluation and application."""

    @property
    def workflow_state_repository(self) -> WorkflowStateRepository:
        """Return the injected workflow-state repository."""
        ...

    @property
    def runtime_event_repository(self) -> RuntimeEventRepository:
        """Return the injected runtime-event repository."""
        ...

    @property
    def execution_package_resolution_service(self) -> ExecutionPackageResolutionService:
        """Return the injected execution-package resolution service."""
        ...

    @property
    def workflow_transition_policy(self) -> WorkflowTransitionPolicy:
        """Return the injected transition policy."""
        ...

    @property
    def acceptance_policy(self) -> AcceptancePolicy:
        """Return the injected acceptance policy."""
        ...

    @property
    def reset_recovery_policy(self) -> ResetRecoveryPolicy:
        """Return the injected reset/recovery policy."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def get_current_workflow_state(self, work_item_id: str) -> WorkflowLifecycleStateView:
        """Return a structured current-state view for one work item."""
        ...

    def evaluate_workflow_transition(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        """Evaluate one proposed workflow transition without mutating workflow truth."""
        ...

    def apply_workflow_transition(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        """Apply one workflow transition when legal."""
        ...

    def detect_workflow_blocks(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        """Return workflow block and repair diagnostics for one request context."""
        ...


__all__ = ['StructuredLogger', 'WorkflowLifecycleService']
