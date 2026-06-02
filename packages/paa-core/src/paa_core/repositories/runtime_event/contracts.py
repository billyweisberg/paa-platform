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
