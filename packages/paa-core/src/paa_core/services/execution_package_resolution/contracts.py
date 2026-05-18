"""Contracts for the execution package resolution service."""

from __future__ import annotations

from typing import Protocol

from paa_core.policies.deployment_capability import DeploymentCapabilityPolicy
from paa_core.repositories.execution_package import ExecutionPackageRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    ExecutionPackageGap,
    ExecutionPackageResolutionRequest,
    ExecutionPackageResolutionView,
)


class ExecutionPackageResolutionService(Protocol):
    """Resolve effective execution-package context for one runtime surface."""

    @property
    def repository(self) -> ExecutionPackageRepository:
        """Return the injected execution-package repository."""

    @property
    def capability_policy(self) -> DeploymentCapabilityPolicy:
        """Return the injected deployment-capability policy."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""

    def resolve_execution_context(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> ExecutionPackageResolutionView:
        """Resolve one normalized execution context from the provided surface identity."""

    def resolve_execution_context_for_surface(
        self,
        execution_surface_key: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        """Resolve one normalized execution context using execution-surface identity."""

    def resolve_execution_context_for_repo_root(
        self,
        repo_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        """Resolve one normalized execution context using repo-root identity."""

    def resolve_execution_context_for_runtime_root(
        self,
        runtime_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        """Resolve one normalized execution context using runtime-root identity."""

    def detect_execution_package_gaps(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> tuple[ExecutionPackageGap, ...]:
        """Return explicit execution-package gaps without mutating install truth."""


__all__ = ['ExecutionPackageResolutionService', 'StructuredLogger']
