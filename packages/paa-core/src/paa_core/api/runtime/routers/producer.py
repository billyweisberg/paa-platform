# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_producer_command_service
from paa_core.application.dto.producer import (
    ProducerDeriveArtifactsRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerPublishAuthorityPackageRequest,
    ProducerSmokeTestRequest,
)
from paa_core.application.services import DefaultProducerCommandApplicationService

router = APIRouter(prefix='/runtime/producer', tags=['runtime-producer'])


class ProducerRepoRootModel(BaseModel):
    repo_root: str


class ProducerPublishAuthorityPackageModel(BaseModel):
    repo_root: str
    project_config: str


class ProducerSmokeTestModel(BaseModel):
    repo_root: str
    output_path: str | None = None


class ProducerLoadIssueModel(BaseModel):
    repo_root: str
    project_config: str
    issue_number: int
    verification_key_prefix: str | None = None
    scope_authority_label: str | None = None
    dry_run: bool = False


class ProducerMaterializeVerificationObligationsModel(BaseModel):
    repo_root: str
    project_config: str
    issue_number: int
    package_path: str | None = None
    verification_key_prefix: str | None = None
    scope_authority_label: str | None = None
    dry_run: bool = False


@router.post('/derive-artifacts')
def derive_artifacts(
    request: ProducerRepoRootModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.derive_artifacts(
        ProducerDeriveArtifactsRequest(repo_root=Path(request.repo_root).resolve())
    ).payload


@router.post('/publish-authority-package')
def publish_authority_package(
    request: ProducerPublishAuthorityPackageModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.publish_authority_package(
        ProducerPublishAuthorityPackageRequest(
            repo_root=Path(request.repo_root).resolve(),
            project_config=Path(request.project_config).resolve(),
        )
    ).payload


@router.post('/smoke-test')
def smoke_test(
    request: ProducerSmokeTestModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.smoke_test(
        ProducerSmokeTestRequest(
            repo_root=Path(request.repo_root).resolve(),
            output_path=Path(request.output_path).resolve() if request.output_path else None,
        )
    ).payload


@router.post('/load-issue-into-paa')
def load_issue_into_paa_route(
    request: ProducerLoadIssueModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.load_issue_into_paa(
        ProducerLoadIssueRequest(
            repo_root=Path(request.repo_root).resolve(),
            project_config=Path(request.project_config).resolve(),
            issue_number=request.issue_number,
            verification_key_prefix=request.verification_key_prefix,
            scope_authority_label=request.scope_authority_label,
            dry_run=request.dry_run,
        )
    ).payload


@router.post('/materialize-verification-obligations')
def materialize_verification_obligations_route(
    request: ProducerMaterializeVerificationObligationsModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.materialize_verification_obligations(
        ProducerMaterializeVerificationObligationsRequest(
            repo_root=Path(request.repo_root).resolve(),
            project_config=Path(request.project_config).resolve(),
            issue_number=request.issue_number,
            package_path=Path(request.package_path).resolve() if request.package_path else None,
            verification_key_prefix=request.verification_key_prefix,
            scope_authority_label=request.scope_authority_label,
            dry_run=request.dry_run,
        )
    ).payload


__all__ = ['router']
