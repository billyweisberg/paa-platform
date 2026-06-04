from __future__ import annotations

from paa_core.application.dto.producer import (
    ProducerDeriveArtifactsRequest,
    ProducerDeriveDesignPackageRequest,
    ProducerDeriveImplementationPlanRequest,
    ProducerEvaluateDerivationReadinessRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeComponentSpecRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerOperationResult,
    ProducerPublishAuthorityPackageRequest,
    ProducerSmokeTestRequest,
)
from paa_core.config import load_producer_project_config
from paa_producer.component_spec_materializer import materialize_component_spec
from paa_producer.derivation_readiness import evaluate_derivation_readiness
from paa_producer.design_package_deriver import derive_design_package
from paa_producer.implementation_plan_deriver import derive_implementation_plan
from paa_core.producer.derive_artifacts import derive_inventory
from paa_core.producer.issue_loader import load_issue_into_paa
from paa_core.producer.obligation_loader import materialize_verification_obligations
from paa_core.producer.publish import publish_from_project_config
from paa_core.producer.smoke_test import run_smoke_test


class DefaultProducerCommandApplicationService:
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
