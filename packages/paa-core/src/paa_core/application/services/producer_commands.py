from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

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
    ProducerOperationResult,
    ProducerPrepareArchitectPacketRequest,
    ProducerPublishAuthorityPackageRequest,
    ProducerReviewCoderBriefRequest,
    ProducerSetImplementationPlanActivityStateRequest,
    ProducerSmokeTestRequest,
)
from paa_core.runtime.support.config import load_producer_project_config
from paa_core.producer.readiness import main as readiness_main
from paa_core.producer.architect_packet_preparer import PacketPreparationOptions, prepare_architect_packet
from paa_core.producer.authority_runtime import main as authority_main
from paa_core.producer.brief_reviewer import review_coder_brief
from paa_core.producer.brief_target_author import author_brief_targets
from paa_core.producer.component_spec_materializer import materialize_component_spec
from paa_core.producer.coder_brief_assembler import assemble_coder_brief
from paa_core.producer.derivation_readiness import evaluate_derivation_readiness
from paa_core.producer.design_package_deriver import derive_design_package
from paa_core.producer.implementation_plan_deriver import derive_implementation_plan
from paa_core.producer.implementation_plan_activity_state import set_implementation_plan_activity_state
from paa_core.producer.implementation_plan_progress import (
    derive_next_activity_bundle,
    implementation_plan_progress,
    reconcile_implementation_plan_progress,
)
from paa_core.producer.derive_artifacts import derive_inventory
from paa_core.producer.issue_loader import load_issue_into_paa
from paa_core.producer.obligation_loader import materialize_verification_obligations
from paa_core.producer.publish import publish_from_project_config
from paa_core.producer.smoke_test import run_smoke_test


class DefaultProducerCommandApplicationService:
    def assemble_coder_brief(self, request: ProducerAssembleCoderBriefRequest) -> ProducerOperationResult:
        result = assemble_coder_brief(
            package_path=request.design_package,
            package_schema_path=request.package_schema_path,
            brief_schema_path=request.brief_schema_path,
            project_slug=request.project_slug,
            output_path=request.output_path,
            persist_db=request.persist_db,
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'package_id': result.package_id,
                'brief_id': result.brief_id,
                'package_path': result.package_path,
                'schema_path': result.schema_path,
                'output_path': result.output_path,
                'coder_run_brief_id': result.coder_run_brief_id,
                'design_package_id': result.design_package_id,
                'work_item_id': result.work_item_id,
                'authority_state': result.authority_state,
                'readiness_class': result.readiness_class,
                'persisted': result.persisted,
                'implementation_plan_id': result.implementation_plan_id,
            }
        )

    def author_brief_targets(self, request: ProducerAuthorBriefTargetsRequest) -> ProducerOperationResult:
        result = author_brief_targets(
            package_path=request.design_package,
            package_schema_path=request.package_schema_path,
            brief_schema_path=request.brief_schema_path,
            project_slug=request.project_slug,
            output_path=request.output_path,
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'package_id': result.package_id,
                'package_path': result.package_path,
                'design_package_id': result.design_package_id,
                'coder_run_brief_id': result.coder_run_brief_id,
                'brief_id': result.brief_id,
                'component_id': result.component_id,
                'work_item_id': result.work_item_id,
                'readiness_class': result.readiness_class,
                'output_path': result.output_path,
                'component_element_keys': result.component_element_keys,
                'realization_keys': result.realization_keys,
                'target_ids': result.target_ids,
                'target_count': result.target_count,
                'persisted': result.persisted,
            }
        )

    def derive_artifacts(self, request: ProducerDeriveArtifactsRequest) -> ProducerOperationResult:
        return ProducerOperationResult(payload=derive_inventory(request.repo_root))

    def derive_design_package(self, request: ProducerDeriveDesignPackageRequest) -> ProducerOperationResult:
        result = derive_design_package(
            package_path=request.design_package,
            schema_path=request.schema_path,
            project_slug=request.project_slug,
            project_name=request.project_name,
            repo_root=request.repo_root,
            dry_run=request.dry_run,
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'package_id': result.package_id,
                'package_path': result.package_path,
                'schema_path': result.schema_path,
                'authority_version': result.authority_version,
                'project_id': result.project_id,
                'authority_version_id': result.authority_version_id,
                'spec_fragment_id': result.spec_fragment_id,
                'implementation_target_id': result.implementation_target_id,
                'component_id': result.component_id,
                'work_item_id': result.work_item_id,
                'design_package_id': result.design_package_id,
                'dry_run': result.dry_run,
            }
        )

    def evaluate_derivation_readiness(
        self,
        request: ProducerEvaluateDerivationReadinessRequest,
    ) -> ProducerOperationResult:
        result = evaluate_derivation_readiness(
            package_path=request.design_package,
            schema_path=request.schema_path,
            project_slug=request.project_slug,
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'package_id': result.package_id,
                'package_path': result.package_path,
                'schema_path': result.schema_path,
                'design_package_id': result.design_package_id,
                'work_item_id': result.work_item_id,
                'authority_version_id': result.authority_version_id,
                'spec_fragment_id': result.spec_fragment_id,
                'implementation_target_id': result.implementation_target_id,
                'component_id': result.component_id,
                'primary_component_name': result.primary_component_name,
                'readiness_class': result.readiness_class,
                'ready': result.ready,
                'blockers': result.blockers,
                'warnings': result.warnings,
                'checks': result.checks,
                'recommendations': result.recommendations,
                'evaluation_mode': result.evaluation_mode,
            }
        )

    def derive_implementation_plan(
        self,
        request: ProducerDeriveImplementationPlanRequest,
    ) -> ProducerOperationResult:
        result = derive_implementation_plan(
            package_path=request.design_package,
            package_schema_path=request.package_schema_path,
            project_slug=request.project_slug,
            consumer_context_key=request.consumer_context_key,
            output_path=request.output_path,
            persist_db=request.persist_db,
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'package_id': result.package_id,
                'package_path': result.package_path,
                'design_package_id': result.design_package_id,
                'implementation_plan_id': result.implementation_plan_id,
                'plan_id_external': result.plan_id_external,
                'consumer_context_key': result.consumer_context_key,
                'activity_count': result.activity_count,
                'dependency_count': result.dependency_count,
                'verification_surface_count': result.verification_surface_count,
                'output_path': result.output_path,
                'persisted': result.persisted,
            }
        )

    def implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        return ProducerOperationResult(payload=implementation_plan_progress(plan_id=request.plan_id))

    def derive_next_activity_bundle(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        return ProducerOperationResult(payload=derive_next_activity_bundle(plan_id=request.plan_id))

    def reconcile_implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        return ProducerOperationResult(payload=reconcile_implementation_plan_progress(plan_id=request.plan_id))

    def set_implementation_plan_activity_state(
        self,
        request: ProducerSetImplementationPlanActivityStateRequest,
    ) -> ProducerOperationResult:
        return ProducerOperationResult(
            payload=set_implementation_plan_activity_state(
                plan_id=request.plan_id,
                activity_key=request.activity_key,
                activity_state=request.activity_state,
                blocking_reason=request.blocking_reason,
                started_at=request.started_at,
                completed_at=request.completed_at,
                metadata_json=request.metadata_json,
            )
        )

    def review_coder_brief(self, request: ProducerReviewCoderBriefRequest) -> ProducerOperationResult:
        result = review_coder_brief(
            coder_run_brief_id=request.coder_run_brief_id,
            design_package_path=request.design_package,
            decision=request.decision,
            notes=request.notes,
            review_summary=request.review_summary,
            output_path=request.output_path,
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'coder_run_brief_id': result.coder_run_brief_id,
                'brief_id': result.brief_id,
                'authority_state': result.authority_state,
                'status': result.status,
                'decision': result.decision,
                'transition_applied': result.transition_applied,
                'target_count': result.target_count,
                'approval_json': result.approval_json,
                'output_path': result.output_path,
                'checks': result.checks,
            }
        )

    def prepare_architect_packet(self, request: ProducerPrepareArchitectPacketRequest) -> ProducerOperationResult:
        result = prepare_architect_packet(
            options=PacketPreparationOptions(
                manifest_path=request.manifest_path,
                package_path=request.design_package,
                packet_output_path=request.packet_output,
                brief_output_path=request.brief_output,
                repo=request.repo,
                branch=request.branch,
                accepted_pr_number=request.accepted_pr_number,
                accepted_pr_url=request.accepted_pr_url,
                closed_issue_number=request.closed_issue_number,
                closed_issue_url=request.closed_issue_url,
                next_issue_number=request.next_issue_number,
                next_issue_url=request.next_issue_url,
                baseline_file=request.baseline_file,
                review_output_path=request.review_output,
                schema_path=request.schema_path,
                project_slug=request.project_slug,
                packet_project=request.packet_project,
                remaining_gap=request.remaining_gap,
                next_move=request.next_move,
                focus=request.focus,
                keep_stable=request.keep_stable,
                governance_reminder=request.governance_reminder,
                pr_starter_branch=request.pr_starter_branch,
                pr_starter_title=request.pr_starter_title,
                pr_starter_body_linkage=request.pr_starter_body_linkage,
                message_id=request.message_id,
                correlation_id=request.correlation_id,
                created_at=request.created_at,
                persist_db=request.persist_db,
            )
        )
        return ProducerOperationResult(
            payload={
                'ok': True,
                'project_slug': result.project_slug,
                'package_id_external': result.package_id_external,
                'coder_run_brief_id': result.coder_run_brief_id,
                'brief_id_external': result.brief_id_external,
                'authority_state': result.authority_state,
                'status': result.status,
                'transition_applied': result.transition_applied,
                'packet_output_path': result.packet_output_path,
                'brief_output_path': result.brief_output_path,
                'review_output_path': result.review_output_path,
                'packet_schema_path': result.packet_schema_path,
                'brief_schema_path': result.brief_schema_path,
                'message_id': result.message_id,
                'target_count': result.target_count,
                'packet_preparation_json': result.packet_preparation_json,
                'checks': result.checks,
            }
        )

    def materialize_readiness(self, request: ProducerMaterializeReadinessRequest) -> ProducerOperationResult:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = readiness_main(request.argv)
        payload = json.loads(stdout.getvalue())
        return ProducerOperationResult(payload=payload, exit_code=exit_code)

    def authority_command(self, request: ProducerAuthorityCommandRequest) -> ProducerOperationResult:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = authority_main(list(request.argv))
        raw = stdout.getvalue().strip()
        payload = {'ok': exit_code in {0, None}, 'output': raw}
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(parsed, dict):
                    payload = parsed
                else:
                    payload = {'ok': exit_code in {0, None}, 'output': parsed}
        return ProducerOperationResult(payload=payload, exit_code=int(exit_code) if exit_code is not None else 0)

    def materialize_component_spec(self, request: ProducerMaterializeComponentSpecRequest) -> ProducerOperationResult:
        result = materialize_component_spec(
            spec_path=request.spec,
            project_slug=request.project_slug,
            anchor_design_package_external=request.anchor_design_package_external,
            anchor_consumer_context_key=request.anchor_consumer_context_key,
        )
        return ProducerOperationResult(
            payload={
                'source_path': result.source_path,
                'project_id': result.project_id,
                'design_package_id': result.design_package_id,
                'component_id': result.component_id,
                'implementation_plan_id': result.implementation_plan_id,
                'plan_id_external': result.plan_id_external,
                'consumer_context_key': result.consumer_context_key,
                'component_element_keys': result.component_element_keys,
                'realization_keys': result.realization_keys,
                'activity_keys': result.activity_keys,
            }
        )

    def publish_authority_package(self, request: ProducerPublishAuthorityPackageRequest) -> ProducerOperationResult:
        config = load_producer_project_config(request.project_config)
        result = publish_from_project_config(repo_root=request.repo_root, config=config)
        return ProducerOperationResult(
            payload={
                'ok': True,
                'package_root': str(result.package_root),
                'metadata_path': str(result.metadata_path),
                'manifest_path': str(result.manifest_path),
                'authority_version': result.authority_version,
            }
        )

    def smoke_test(self, request: ProducerSmokeTestRequest) -> ProducerOperationResult:
        return ProducerOperationResult(payload=run_smoke_test(request.repo_root, output_path=request.output_path))

    def load_issue_into_paa(self, request: ProducerLoadIssueRequest) -> ProducerOperationResult:
        config = load_producer_project_config(request.project_config)
        return ProducerOperationResult(
            payload=load_issue_into_paa(
                repo_root=request.repo_root,
                config=config,
                issue_number=request.issue_number,
                verification_key_prefix=request.verification_key_prefix,
                scope_authority_label=request.scope_authority_label,
                dry_run=request.dry_run,
            )
        )

    def materialize_verification_obligations(
        self,
        request: ProducerMaterializeVerificationObligationsRequest,
    ) -> ProducerOperationResult:
        config = load_producer_project_config(request.project_config)
        return ProducerOperationResult(
            payload=materialize_verification_obligations(
                repo_root=request.repo_root,
                config=config,
                issue_number=request.issue_number,
                package_path=request.package_path,
                verification_key_prefix=request.verification_key_prefix,
                scope_authority_label=request.scope_authority_label,
                dry_run=request.dry_run,
            )
        )
