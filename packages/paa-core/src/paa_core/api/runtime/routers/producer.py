# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_producer_command_service
from paa_core.application.dto.producer import (
    ProducerAssembleCoderBriefRequest,
    ProducerAuthorityCommandRequest,
    ProducerAuthorBriefTargetsRequest,
    ProducerDeriveArtifactsRequest,
    ProducerDeriveDesignPackageRequest,
    ProducerDeriveImplementationPlanRequest,
    ProducerEvaluateDerivationReadinessRequest,
    ProducerImplementationPlanProgressRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeReadinessRequest,
    ProducerMaterializeComponentSpecRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerPublishAuthorityPackageRequest,
    ProducerPrepareArchitectPacketRequest,
    ProducerReviewCoderBriefRequest,
    ProducerSetImplementationPlanActivityStateRequest,
    ProducerSmokeTestRequest,
)
from paa_core.application.services import DefaultProducerCommandApplicationService

router = APIRouter(prefix='/runtime/producer', tags=['runtime-producer'])


class ProducerRepoRootModel(BaseModel):
    repo_root: str


class ProducerAssembleCoderBriefModel(BaseModel):
    design_package: str
    package_schema_path: str | None = None
    brief_schema_path: str | None = None
    project_slug: str | None = None
    output_path: str | None = None
    persist_db: bool = True


class ProducerAuthorBriefTargetsModel(BaseModel):
    design_package: str
    package_schema_path: str | None = None
    brief_schema_path: str | None = None
    project_slug: str | None = None
    output_path: str | None = None


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


class ProducerReviewCoderBriefModel(BaseModel):
    coder_run_brief_id: str | None = None
    design_package: str | None = None
    decision: str
    notes: str | None = None
    review_summary: str | None = None
    output_path: str | None = None


class ProducerPrepareArchitectPacketModel(BaseModel):
    manifest_path: str
    design_package: str
    packet_output: str
    brief_output: str
    repo: str
    accepted_pr_number: int
    accepted_pr_url: str
    closed_issue_number: int
    closed_issue_url: str
    next_issue_number: int
    next_issue_url: str
    baseline_file: str
    branch: str = 'main'
    review_output: str | None = None
    schema_path: str | None = None
    project_slug: str | None = None
    packet_project: str | None = None
    remaining_gap: str | None = None
    next_move: list[str] = []
    focus: list[str] = []
    keep_stable: list[str] = []
    governance_reminder: list[str] = []
    pr_starter_branch: str | None = None
    pr_starter_title: str | None = None
    pr_starter_body_linkage: str | None = None
    message_id: str | None = None
    correlation_id: str | None = None
    created_at: str | None = None
    persist_db: bool = True


class ProducerArgvModel(BaseModel):
    argv: list[str]


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


@router.post('/assemble-coder-brief')
def assemble_coder_brief_route(
    request: ProducerAssembleCoderBriefModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.assemble_coder_brief(
        ProducerAssembleCoderBriefRequest(
            design_package=Path(request.design_package).resolve(),
            package_schema_path=Path(request.package_schema_path).resolve() if request.package_schema_path else None,
            brief_schema_path=Path(request.brief_schema_path).resolve() if request.brief_schema_path else None,
            project_slug=request.project_slug,
            output_path=Path(request.output_path).resolve() if request.output_path else None,
            persist_db=request.persist_db,
        )
    ).payload


@router.post('/author-brief-targets')
def author_brief_targets_route(
    request: ProducerAuthorBriefTargetsModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.author_brief_targets(
        ProducerAuthorBriefTargetsRequest(
            design_package=Path(request.design_package).resolve(),
            package_schema_path=Path(request.package_schema_path).resolve() if request.package_schema_path else None,
            brief_schema_path=Path(request.brief_schema_path).resolve() if request.brief_schema_path else None,
            project_slug=request.project_slug,
            output_path=Path(request.output_path).resolve() if request.output_path else None,
        )
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


@router.post('/review-coder-brief')
def review_coder_brief_route(
    request: ProducerReviewCoderBriefModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.review_coder_brief(
        ProducerReviewCoderBriefRequest(
            coder_run_brief_id=request.coder_run_brief_id,
            design_package=Path(request.design_package).resolve() if request.design_package else None,
            decision=request.decision,
            notes=request.notes,
            review_summary=request.review_summary,
            output_path=Path(request.output_path).resolve() if request.output_path else None,
        )
    ).payload


@router.post('/prepare-architect-packet')
def prepare_architect_packet_route(
    request: ProducerPrepareArchitectPacketModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.prepare_architect_packet(
        ProducerPrepareArchitectPacketRequest(
            manifest_path=Path(request.manifest_path).resolve(),
            design_package=Path(request.design_package).resolve(),
            packet_output=Path(request.packet_output).resolve(),
            brief_output=Path(request.brief_output).resolve(),
            repo=request.repo,
            accepted_pr_number=request.accepted_pr_number,
            accepted_pr_url=request.accepted_pr_url,
            closed_issue_number=request.closed_issue_number,
            closed_issue_url=request.closed_issue_url,
            next_issue_number=request.next_issue_number,
            next_issue_url=request.next_issue_url,
            baseline_file=Path(request.baseline_file).resolve(),
            branch=request.branch,
            review_output=Path(request.review_output).resolve() if request.review_output else None,
            schema_path=Path(request.schema_path).resolve() if request.schema_path else None,
            project_slug=request.project_slug,
            packet_project=request.packet_project,
            remaining_gap=request.remaining_gap,
            next_move=tuple(request.next_move),
            focus=tuple(request.focus),
            keep_stable=tuple(request.keep_stable),
            governance_reminder=tuple(request.governance_reminder),
            pr_starter_branch=request.pr_starter_branch,
            pr_starter_title=request.pr_starter_title,
            pr_starter_body_linkage=request.pr_starter_body_linkage,
            message_id=request.message_id,
            correlation_id=request.correlation_id,
            created_at=request.created_at,
            persist_db=request.persist_db,
        )
    ).payload


@router.post('/materialize-readiness')
def materialize_readiness_route(
    request: ProducerArgvModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.materialize_readiness(
        ProducerMaterializeReadinessRequest(argv=tuple(request.argv))
    ).payload


@router.post('/authority')
def authority_command_route(
    request: ProducerArgvModel,
    service: DefaultProducerCommandApplicationService = Depends(get_producer_command_service),
) -> dict[str, object]:
    return service.authority_command(
        ProducerAuthorityCommandRequest(argv=tuple(request.argv))
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
