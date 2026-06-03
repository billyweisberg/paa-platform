from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProducerOperationResult:
    payload: dict[str, Any]
    exit_code: int = 0


@dataclass(frozen=True)
class ProducerDeriveArtifactsRequest:
    repo_root: Path


@dataclass(frozen=True)
class ProducerPublishAuthorityPackageRequest:
    repo_root: Path
    project_config: Path


@dataclass(frozen=True)
class ProducerSmokeTestRequest:
    repo_root: Path
    output_path: Path | None = None


@dataclass(frozen=True)
class ProducerLoadIssueRequest:
    repo_root: Path
    project_config: Path
    issue_number: int
    verification_key_prefix: str | None = None
    scope_authority_label: str | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class ProducerMaterializeVerificationObligationsRequest:
    repo_root: Path
    project_config: Path
    issue_number: int
    package_path: Path | None = None
    verification_key_prefix: str | None = None
    scope_authority_label: str | None = None
    dry_run: bool = False
