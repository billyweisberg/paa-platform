# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_producer_command_service
from paa_core.application.dto.producer import (
    ProducerDeriveArtifactsRequest,
    ProducerDeriveDesignPackageRequest,
    ProducerDeriveImplementationPlanRequest,
    ProducerEvaluateDerivationReadinessRequest,
    ProducerImplementationPlanProgressRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeComponentSpecRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerPublishAuthorityPackageRequest,
    ProducerSetImplementationPlanActivityStateRequest,
    ProducerSmokeTestRequest,
)
from paa_core.application.services import DefaultProducerCommandApplicationService

router = APIRouter(prefix='/runtime/producer', tags=['runtime-producer'])


class ProducerRepoRootModel(BaseModel):
    repo_root: str


class ProducerPublishAuthorityPackageModel(BaseModel):
    repo_root: str
    project_config: str


class ProducerDeriveDesignPackageModel(BaseModel):
    repo_root: str
    design_package: str
    schema_path: str | None = None
    project_slug: str | None = None
    project_name: str | None = None
    dry_run: bool = False


class ProducerEvaluateDerivationReadinessModel(BaseModel):
    design_package: str
    schema_path: str | None = None
    project_slug: str | None = None


class ProducerDeriveImplementationPlanModel(BaseModel):
    design_package: str
    package_schema_path: str | None = None
    project_slug: str | None = None
    consumer_context_key: str = 'python'
    output_path: str | None = None
    persist_db: bool = True


class ProducerMaterializeComponentSpecModel(BaseModel):
    spec: str
    project_slug: str
    anchor_design_package_external: str
    anchor_consumer_context_key: str


class ProducerImplementationPlanProgressModel(BaseModel):
    plan_id: str


class ProducerSetImplementationPlanActivityStateModel(BaseModel):
    plan_id: str
    activity_key: str
    activity_state: str
    blocking_reason: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    metadata_json: str | None = None


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


@router.post('/derive-design-package')
def derive_design_package_route(
    request: ProducerDeriveDesignPackageModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.derive_design_package(
        ProducerDeriveDesignPackageRequest(
            repo_root=Path(request.repo_root).resolve(),
            design_package=Path(request.design_package).resolve(),
            schema_path=Path(request.schema_path).resolve() if request.schema_path else None,
            project_slug=request.project_slug,
            project_name=request.project_name,
            dry_run=request.dry_run,
        )
    ).payload


@router.post('/evaluate-derivation-readiness')
def evaluate_derivation_readiness_route(
    request: ProducerEvaluateDerivationReadinessModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.evaluate_derivation_readiness(
        ProducerEvaluateDerivationReadinessRequest(
            design_package=Path(request.design_package).resolve(),
            schema_path=Path(request.schema_path).resolve() if request.schema_path else None,
            project_slug=request.project_slug,
        )
    ).payload


@router.post('/derive-implementation-plan')
def derive_implementation_plan_route(
    request: ProducerDeriveImplementationPlanModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.derive_implementation_plan(
        ProducerDeriveImplementationPlanRequest(
            design_package=Path(request.design_package).resolve(),
            package_schema_path=Path(request.package_schema_path).resolve() if request.package_schema_path else None,
            project_slug=request.project_slug,
            consumer_context_key=request.consumer_context_key,
            output_path=Path(request.output_path).resolve() if request.output_path else None,
            persist_db=request.persist_db,
        )
    ).payload


@router.post('/materialize-component-spec')
def materialize_component_spec_route(
    request: ProducerMaterializeComponentSpecModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.materialize_component_spec(
        ProducerMaterializeComponentSpecRequest(
            spec=Path(request.spec).resolve(),
            project_slug=request.project_slug,
            anchor_design_package_external=request.anchor_design_package_external,
            anchor_consumer_context_key=request.anchor_consumer_context_key,
        )
    ).payload


@router.post('/implementation-plan-progress')
def implementation_plan_progress_route(
    request: ProducerImplementationPlanProgressModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.implementation_plan_progress(
        ProducerImplementationPlanProgressRequest(plan_id=request.plan_id)
    ).payload


@router.post('/derive-next-activity-bundle')
def derive_next_activity_bundle_route(
    request: ProducerImplementationPlanProgressModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.derive_next_activity_bundle(
        ProducerImplementationPlanProgressRequest(plan_id=request.plan_id)
    ).payload


@router.post('/reconcile-implementation-plan-progress')
def reconcile_implementation_plan_progress_route(
    request: ProducerImplementationPlanProgressModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.reconcile_implementation_plan_progress(
        ProducerImplementationPlanProgressRequest(plan_id=request.plan_id)
    ).payload


@router.post('/set-implementation-plan-activity-state')
def set_implementation_plan_activity_state_route(
    request: ProducerSetImplementationPlanActivityStateModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.set_implementation_plan_activity_state(
        ProducerSetImplementationPlanActivityStateRequest(
            plan_id=request.plan_id,
            activity_key=request.activity_key,
            activity_state=request.activity_state,
            blocking_reason=request.blocking_reason,
            started_at=request.started_at,
            completed_at=request.completed_at,
            metadata_json=request.metadata_json,
        )
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
