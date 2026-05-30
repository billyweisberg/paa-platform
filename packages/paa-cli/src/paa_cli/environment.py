"""Environment-resolution support for the PAA operator CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import OperatorInvocationContext


@dataclass(frozen=True)
class EnvironmentResolutionInput:
    """Inputs used to resolve one CLI invocation context."""

    repo_root: str | None = None
    output_mode: str = 'table'
    dry_run: bool = False
    strict_mode: bool = True
    metadata: dict[str, Any] | None = None


class EnvironmentResolver:
    """Resolve a stable invocation context for one CLI run."""

    def resolve(self, request: EnvironmentResolutionInput | None = None) -> OperatorInvocationContext:
        request = request or EnvironmentResolutionInput()
        repo_root = self._resolve_repo_root(request.repo_root)
        metadata = dict(request.metadata or {})
        metadata.setdefault('resolved_repo_root', repo_root)
        return OperatorInvocationContext(
            repo_root=repo_root,
            output_mode=request.output_mode,
            dry_run=request.dry_run,
            strict_mode=request.strict_mode,
            metadata=metadata,
        )

    @staticmethod
    def _resolve_repo_root(repo_root: str | None) -> str:
        if repo_root:
            return str(Path(repo_root).resolve())
        return str(Path.cwd().resolve())


__all__ = ['EnvironmentResolutionInput', 'EnvironmentResolver']
