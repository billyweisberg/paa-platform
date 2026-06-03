from __future__ import annotations

from paa_core.application.dto.producer import (
    ProducerDeriveArtifactsRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerOperationResult,
    ProducerPublishAuthorityPackageRequest,
    ProducerSmokeTestRequest,
)
from paa_core.config import load_producer_project_config
from paa_core.producer.derive_artifacts import derive_inventory
from paa_core.producer.issue_loader import load_issue_into_paa
from paa_core.producer.obligation_loader import materialize_verification_obligations
from paa_core.producer.publish import publish_from_project_config
from paa_core.producer.smoke_test import run_smoke_test


class DefaultProducerCommandApplicationService:
    def derive_artifacts(self, request: ProducerDeriveArtifactsRequest) -> ProducerOperationResult:
        return ProducerOperationResult(payload=derive_inventory(request.repo_root))

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
