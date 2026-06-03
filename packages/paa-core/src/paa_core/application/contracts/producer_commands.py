from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.producer import (
    ProducerDeriveArtifactsRequest,
    ProducerLoadIssueRequest,
    ProducerMaterializeVerificationObligationsRequest,
    ProducerOperationResult,
    ProducerPublishAuthorityPackageRequest,
    ProducerSmokeTestRequest,
)


class ProducerCommandService(Protocol):
    def derive_artifacts(self, request: ProducerDeriveArtifactsRequest) -> ProducerOperationResult: ...
    def publish_authority_package(self, request: ProducerPublishAuthorityPackageRequest) -> ProducerOperationResult: ...
    def smoke_test(self, request: ProducerSmokeTestRequest) -> ProducerOperationResult: ...
    def load_issue_into_paa(self, request: ProducerLoadIssueRequest) -> ProducerOperationResult: ...
    def materialize_verification_obligations(
        self,
        request: ProducerMaterializeVerificationObligationsRequest,
    ) -> ProducerOperationResult: ...
