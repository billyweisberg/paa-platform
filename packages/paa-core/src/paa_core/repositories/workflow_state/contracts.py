"""Contracts for workflow-state repository access."""

from __future__ import annotations

from typing import Protocol

from .models import (
    QueueClaimRecord,
    WorkflowStateRecord,
    WorkflowStateUpsertSpec,
    WorkflowTransitionAppendSpec,
    WorkflowTransitionRecord,
)


class WorkflowStateRepository(Protocol):
    """Persistence boundary for DB-primary workflow truth."""

    def get_workflow_state(self, workflow_state_id: str) -> WorkflowStateRecord | None:
        """Return one workflow state by primary id."""

    def get_workflow_state_for_work_item(self, work_item_id: str) -> WorkflowStateRecord | None:
        """Return the current workflow state for one work item."""

    def list_workflow_transitions_for_work_item(
        self, work_item_id: str
    ) -> list[WorkflowTransitionRecord]:
        """Return transition history for one work item."""

    def get_active_queue_claim_for_message(self, queue_message_id: str) -> QueueClaimRecord | None:
        """Return the active queue claim for one queue message when present."""

    def upsert_workflow_state(self, spec: WorkflowStateUpsertSpec) -> None:
        """Create or update the current workflow state for one work item."""

    def append_workflow_transition(self, spec: WorkflowTransitionAppendSpec) -> None:
        """Append one workflow transition history row."""


__all__ = ['WorkflowStateRepository']
