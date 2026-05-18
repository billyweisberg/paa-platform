"""Models for the reset recovery policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResetRecoveryRequest:
    work_item_id: str
    workflow_stage: str | None
    transition_status: str | None = None
    retry_requested: bool = False
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ResetRecoveryEvaluationContext:
    state_consistency: str | None
    blocking_reason_code: str | None = None
    active_claim_status: str | None = None
    execution_surface_key: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ResetRecoveryDecision:
    requires_manual_repair: bool
    should_reset: bool
    should_retry: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any]


__all__ = [
    'ResetRecoveryDecision',
    'ResetRecoveryEvaluationContext',
    'ResetRecoveryRequest',
]
