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


@dataclass(frozen=True)
class ProducerDeriveDesignPackageRequest:
    repo_root: Path
    design_package: Path
    schema_path: Path | None = None
    project_slug: str | None = None
    project_name: str | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class ProducerEvaluateDerivationReadinessRequest:
    design_package: Path
    schema_path: Path | None = None
    project_slug: str | None = None


@dataclass(frozen=True)
class ProducerDeriveImplementationPlanRequest:
    design_package: Path
    package_schema_path: Path | None = None
    project_slug: str | None = None
    consumer_context_key: str = 'python'
    output_path: Path | None = None
    persist_db: bool = True


@dataclass(frozen=True)
class ProducerMaterializeComponentSpecRequest:
    spec: Path
    project_slug: str
    anchor_design_package_external: str
    anchor_consumer_context_key: str


@dataclass(frozen=True)
class ProducerImplementationPlanProgressRequest:
    plan_id: str


@dataclass(frozen=True)
class ProducerSetImplementationPlanActivityStateRequest:
    plan_id: str
    activity_key: str
    activity_state: str
    blocking_reason: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    metadata_json: str | None = None
