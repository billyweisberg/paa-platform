"""Contracts for runtime-event repository access."""

from __future__ import annotations

from typing import Protocol

from .models import (
    AcceptanceEventRecord,
    AutomationRunEventRecord,
    AutomationRunRecord,
    HandoffRecord,
    QueueMessageRecord,
    TransitionInputRecord,
)


class RuntimeEventRepository(Protocol):
    """Read-oriented access boundary for runtime transport and execution evidence."""

    def resolve_work_item_id_for_message(self, message: dict[str, object]) -> str | None:
        """Return one work item id resolved from one runtime packet envelope."""

    def find_packet_compilation_run(
        self,
        *,
        message_id_external: str,
        schema_type: str,
    ) -> AutomationRunRecord | None:
        """Return the latest packet-compilation run for one message id and schema type."""

    def create_packet_compilation_run_for_message(
        self,
        *,
        message: dict[str, object],
        message_file: str,
        agent_name: str,
        work_item_id: str | None = None,
    ) -> AutomationRunRecord | None:
        """Persist one packet-compilation automation run for one outbound packet."""

    def record_queue_send_for_message(
        self,
        *,
        message: dict[str, object],
        queue_name: str,
        exchange: str,
        publish_result: dict[str, object] | None = None,
        work_item_id: str | None = None,
        packet_compilation_run: AutomationRunRecord | None = None,
    ) -> QueueMessageRecord | None:
        """Persist one queue send/handoff record for one outbound packet."""

    def update_queue_message_status_by_external(
        self,
        *,
        message_id_external: str,
        queue_status: str,
        handoff_status: str,
        timestamp_field: str,
    ) -> None:
        """Update one queue message and linked handoff status by stable external message id."""

    def resolve_verification_obligation(
        self,
        *,
        project_slug: str,
        issue_number: int,
        verification_key_suffix: str | None = None,
        verification_type: str | None = None,
    ) -> tuple[str, str] | None:
        """Resolve one verification obligation by issue and either key suffix or verification type."""

    def record_evidence_if_missing(
        self,
        *,
        project_slug: str,
        issue_number: int,
        verification_id: str,
        agent_name: str,
        result: str,
        summary: str,
        artifact_location: str,
        metadata: dict[str, object],
        captured_at: str | None,
    ) -> None:
        """Persist one evidence row when the artifact location has not already been recorded."""

    def record_acceptance_event_if_missing(
        self,
        *,
        project_slug: str,
        issue_number: int,
        agent_name: str,
        role_name: str,
        decision: str,
        notes: str,
        metadata: dict[str, object],
        created_at: str | None,
    ) -> None:
        """Persist one acceptance event when an equivalent notes record does not already exist."""

    def get_handoff(self, handoff_id: str) -> HandoffRecord | None:
        """Return one handoff by primary id."""

    def get_queue_message(self, queue_message_id: str) -> QueueMessageRecord | None:
        """Return one queue message by primary id."""

    def get_queue_message_by_external(self, message_id_external: str) -> QueueMessageRecord | None:
        """Return one queue message by stable external message id."""

    def get_automation_run(self, automation_run_id: str) -> AutomationRunRecord | None:
        """Return one automation run by primary id."""

    def get_latest_automation_run_for_message_id(self, message_id_external: str) -> AutomationRunRecord | None:
        """Return the latest automation run whose artifacts are bound to one stable external message id."""

    def list_transition_inputs_for_work_item(self, work_item_id: str) -> list[TransitionInputRecord]:
        """Return transition inputs for one work item in captured order."""

    def list_automation_run_events(self, automation_run_id: str) -> list[AutomationRunEventRecord]:
        """Return append-only run events for one automation run."""

    def list_acceptance_events_for_work_item(self, work_item_id: str) -> list[AcceptanceEventRecord]:
        """Return acceptance history for one work item."""


__all__ = ['RuntimeEventRepository']
