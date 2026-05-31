"""Contracts for the MethodologyExecution repository."""

from __future__ import annotations

from typing import Protocol

from .models import (
    MethodologyExecutionBindingEntrySpec,
    MethodologyExecutionBindingRecord,
    MethodologyExecutionBindingReplaceSpec,
    MethodologyExecutionEventAppendSpec,
    MethodologyExecutionEventRecord,
    MethodologyExecutionProjectionInputRecord,
    MethodologyExecutionRecord,
    MethodologyExecutionUpsertSpec,
)


class MethodologyExecutionRepository(Protocol):
    """Persistence boundary for methodology execution current truth and history."""

    def get_methodology_execution(self, methodology_execution_id: str) -> MethodologyExecutionRecord | None:
        """Return one methodology execution root by primary id."""
        ...

    def find_methodology_execution_by_primary_ref(
        self,
        project_id: str,
        work_item_id: str,
        component_id: str | None = None,
    ) -> MethodologyExecutionRecord | None:
        """Resolve the current methodology execution by primary business anchors."""
        ...

    def list_methodology_execution_events(
        self, methodology_execution_id: str
    ) -> list[MethodologyExecutionEventRecord]:
        """Return append-only transition events for one methodology execution thread."""
        ...

    def list_methodology_execution_bindings(
        self, methodology_execution_id: str
    ) -> list[MethodologyExecutionBindingRecord]:
        """Return typed bindings for one methodology execution thread."""
        ...

    def load_methodology_execution_projection_inputs(
        self, methodology_execution_id: str
    ) -> MethodologyExecutionProjectionInputRecord:
        """Return stitched repository-side inputs for projection and pointer-status services."""
        ...

    def upsert_methodology_execution(self, spec: MethodologyExecutionUpsertSpec) -> None:
        """Create or update one methodology execution root record."""
        ...

    def append_methodology_execution_event(self, spec: MethodologyExecutionEventAppendSpec) -> None:
        """Append one immutable methodology execution transition event."""
        ...

    def replace_methodology_execution_bindings(self, spec: MethodologyExecutionBindingReplaceSpec) -> None:
        """Replace or upsert typed methodology execution bindings for one execution thread."""
        ...


__all__ = [
    'MethodologyExecutionBindingEntrySpec',
    'MethodologyExecutionRepository',
]
