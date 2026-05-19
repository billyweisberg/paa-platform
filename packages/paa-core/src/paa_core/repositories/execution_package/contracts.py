"""Contracts for the ExecutionPackage repository."""

from __future__ import annotations

from typing import Protocol

from .models import (
    ExecutionPackageInstallRecord,
    ExecutionPackageOverlayRecord,
    InstalledExecutionContextRecord,
)


class ExecutionPackageRepository(Protocol):
    """Read-oriented execution-package access boundary for active resolution."""

    def get_execution_package_install(
        self,
        execution_package_install_id: str,
    ) -> ExecutionPackageInstallRecord | None:
        """Return one install registration by primary id."""
        ...

    def get_active_install_for_execution_surface(
        self,
        execution_surface_key: str,
    ) -> ExecutionPackageInstallRecord | None:
        """Return the active install for one execution surface."""
        ...

    def get_active_install_for_repo_root(
        self,
        repo_root_path: str,
    ) -> ExecutionPackageInstallRecord | None:
        """Return the active install whose repo root matches one runtime surface."""
        ...

    def get_active_install_for_runtime_root(
        self,
        runtime_root_path: str,
    ) -> ExecutionPackageInstallRecord | None:
        """Return the active install whose runtime root matches one runtime surface."""
        ...

    def list_overlays_for_install(
        self,
        execution_package_install_id: str,
    ) -> list[ExecutionPackageOverlayRecord]:
        """Return overlay history for one install."""
        ...

    def list_active_overlays_for_install(
        self,
        execution_package_install_id: str,
    ) -> list[ExecutionPackageOverlayRecord]:
        """Return active overlays for one install."""
        ...

    def resolve_active_execution_context(
        self,
        execution_surface_key: str,
    ) -> InstalledExecutionContextRecord | None:
        """Return the active installed execution context for one execution surface."""
        ...


__all__ = ['ExecutionPackageRepository']
