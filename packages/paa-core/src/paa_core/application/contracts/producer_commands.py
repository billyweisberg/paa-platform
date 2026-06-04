from __future__ import annotations

from typing import Protocol

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


class ProducerCommandService(Protocol):
    def assemble_coder_brief(self, request: ProducerAssembleCoderBriefRequest) -> ProducerOperationResult: ...
    def author_brief_targets(self, request: ProducerAuthorBriefTargetsRequest) -> ProducerOperationResult: ...
    def derive_artifacts(self, request: ProducerDeriveArtifactsRequest) -> ProducerOperationResult: ...
    def derive_design_package(self, request: ProducerDeriveDesignPackageRequest) -> ProducerOperationResult: ...
    def evaluate_derivation_readiness(
        self,
        request: ProducerEvaluateDerivationReadinessRequest,
    ) -> ProducerOperationResult: ...
    def derive_implementation_plan(
        self,
        request: ProducerDeriveImplementationPlanRequest,
    ) -> ProducerOperationResult: ...
    def implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult: ...
    def derive_next_activity_bundle(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult: ...
    def reconcile_implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult: ...
    def set_implementation_plan_activity_state(
        self,
        request: ProducerSetImplementationPlanActivityStateRequest,
    ) -> ProducerOperationResult: ...
    def review_coder_brief(self, request: ProducerReviewCoderBriefRequest) -> ProducerOperationResult: ...
    def prepare_architect_packet(self, request: ProducerPrepareArchitectPacketRequest) -> ProducerOperationResult: ...
    def materialize_readiness(self, request: ProducerMaterializeReadinessRequest) -> ProducerOperationResult: ...
    def authority_command(self, request: ProducerAuthorityCommandRequest) -> ProducerOperationResult: ...
    def materialize_component_spec(
        self,
        request: ProducerMaterializeComponentSpecRequest,
    ) -> ProducerOperationResult: ...
    def publish_authority_package(self, request: ProducerPublishAuthorityPackageRequest) -> ProducerOperationResult: ...
    def smoke_test(self, request: ProducerSmokeTestRequest) -> ProducerOperationResult: ...
    def load_issue_into_paa(self, request: ProducerLoadIssueRequest) -> ProducerOperationResult: ...
    def materialize_verification_obligations(
        self,
        request: ProducerMaterializeVerificationObligationsRequest,
    ) -> ProducerOperationResult: ...
