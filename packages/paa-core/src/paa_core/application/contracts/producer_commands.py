from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.producer import (
    ProducerDeriveArtifactsRequest,
    ProducerDeriveDesignPackageRequest,
    ProducerDeriveImplementationPlanRequest,
    ProducerEvaluateDerivationReadinessRequest,
    ProducerImplementationPlanProgressRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeComponentSpecRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerOperationResult,
    ProducerPublishAuthorityPackageRequest,
    ProducerSetImplementationPlanActivityStateRequest,
    ProducerSmokeTestRequest,
)


class ProducerCommandService(Protocol):
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
