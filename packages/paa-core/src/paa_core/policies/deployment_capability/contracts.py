"""Contracts for the deployment capability policy."""

from __future__ import annotations

from typing import Protocol

from .models import (
    DeploymentCapabilityContext,
    DeploymentCapabilityDecision,
    DeploymentCapabilityRequest,
)


class DeploymentCapabilityPolicy(Protocol):
    """Evaluate whether one resolved execution context satisfies required deployment capability."""

    def evaluate_capability(
        self,
        request: DeploymentCapabilityRequest,
        context: DeploymentCapabilityContext,
    ) -> DeploymentCapabilityDecision:
        """Return an allow/deny decision for the requested deployment capability set."""
        ...


__all__ = ['DeploymentCapabilityPolicy']
