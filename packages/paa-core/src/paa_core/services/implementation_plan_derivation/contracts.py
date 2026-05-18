"""Contracts for the Implementation Plan Derivation service."""

from __future__ import annotations

from typing import Protocol

from .models import ImplementationPlanDerivationRequest, ImplementationPlanDerivationResult


class StructuredLogger(Protocol):
    def info(self, event: str, **fields: object) -> None:
        """Record an informational service event."""

    def warning(self, event: str, **fields: object) -> None:
        """Record a warning service event."""


class ImplementationPlanDerivationService(Protocol):
    """Derive authoritative implementation-plan truth from structured project-design inputs."""

    def derive_plan(self, request: ImplementationPlanDerivationRequest) -> ImplementationPlanDerivationResult:
        """Derive one implementation plan and optionally persist it."""


__all__ = ['ImplementationPlanDerivationService', 'StructuredLogger']
