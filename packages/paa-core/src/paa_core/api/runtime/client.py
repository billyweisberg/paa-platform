from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from paa_core.application.dto.authority import AuthorityInstallRequest, AuthorityInstallResultView
from paa_core.application.contracts.component_taxonomy import ComponentTaxonomyService
from paa_core.application.dto.component_taxonomy import (
    ComponentTaxonomyOperationResult,
    GetRealizationTypeRequest,
    ListElementTypeRealizationLinksRequest,
    ListRealizationTypesRequest,
    UpsertElementTypeRealizationLinkRequest,
    UpsertRealizationTypeRequest,
)
from paa_core.application.dto.queue import (
    QueueCheckRequest,
    QueueClaimActionRequest,
    QueueClaimNextRequest,
    QueueListClaimsRequest,
    QueueOperationResult,
    QueuePacketFileRequest,
    QueuePurgeRequest,
    QueueRepoRootRequest,
    QueueSendRequest,
    QueueValidateRequest,
)
from paa_core.application.dto.operator import (
    OperatorCommand,
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
    OperatorInvocationContext,
    OperatorOutputMessage,
    OperatorOutputSection,
    OperatorOutputTable,
)
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
    ProducerPublishAuthorityPackageRequest,
    ProducerPrepareArchitectPacketRequest,
    ProducerReviewCoderBriefRequest,
    ProducerSetImplementationPlanActivityStateRequest,
    ProducerSmokeTestRequest,
)
from paa_core.application.dto.runtime import (
    RuntimeInstallRequest,
    RuntimeHostRunRequest,
    RuntimeLogsRequest,
    RuntimeOperationResult,
    RuntimeStatusRequest,
    RuntimeSupervisorRequest,
)
from paa_core.application.dto.status import RuntimeSmokeRequest, RuntimeStatusResultView, RuntimeValidationRequest, TechLeadServiceMapResultView
from paa_core.application.dto.workflow import AutomationPreflightRequest, AutomationPreflightResultView
from paa_core.application.services import (
    DefaultAuthorityInstallApplicationService,
    DefaultAutomationPreflightApplicationService,
    DefaultOperatorCommandApplicationService,
    DefaultProducerCommandApplicationService,
    DefaultQueueAdminApplicationService,
    DefaultRuntimeAdminApplicationService,
    DefaultRuntimeInstallApplicationService,
    DefaultRuntimeReportApplicationService,
    DefaultRuntimeValidationApplicationService,
    build_default_operator_command_service,
)


def _to_jsonable(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        dataclass_payload = cast(dict[str, object], asdict(cast(Any, value)))
        return {key: _to_jsonable(item) for key, item in dataclass_payload.items()}
    if isinstance(value, dict):
        dict_payload = cast(dict[object, object], value)
        return {str(key): _to_jsonable(item) for key, item in dict_payload.items()}
    if isinstance(value, (list, tuple)):
        sequence_payload = cast(list[object] | tuple[object, ...], value)
        return [_to_jsonable(item) for item in sequence_payload]
    return value


class RuntimeApiClient(Protocol):
    def install_authority_package(self, request: AuthorityInstallRequest) -> AuthorityInstallResultView: ...
    def install_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult: ...
    def update_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult: ...
    def run_operator_command(self, request: OperatorCommandRequest) -> OperatorCommandResult: ...
    def supports_operator_command_family(self, command_family: str) -> bool: ...
    def list_realization_types(self, request: ListRealizationTypesRequest) -> ComponentTaxonomyOperationResult: ...
    def get_realization_type(self, request: GetRealizationTypeRequest) -> ComponentTaxonomyOperationResult: ...
    def list_element_type_realization_links(
        self, request: ListElementTypeRealizationLinksRequest
    ) -> ComponentTaxonomyOperationResult: ...
    def upsert_element_type_realization_link(
        self, request: UpsertElementTypeRealizationLinkRequest
    ) -> ComponentTaxonomyOperationResult: ...
    def upsert_realization_type(self, request: UpsertRealizationTypeRequest) -> ComponentTaxonomyOperationResult: ...
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
    def producer_smoke_test(self, request: ProducerSmokeTestRequest) -> ProducerOperationResult: ...
    def load_issue_into_paa(self, request: ProducerLoadIssueRequest) -> ProducerOperationResult: ...
    def materialize_verification_obligations(
        self,
        request: ProducerMaterializeVerificationObligationsRequest,
    ) -> ProducerOperationResult: ...
    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult: ...
    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult: ...
    def check(self, request: QueueCheckRequest) -> QueueOperationResult: ...
    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult: ...
    def validate(self, request: QueueValidateRequest) -> QueueOperationResult: ...
    def send(self, request: QueueSendRequest) -> QueueOperationResult: ...
    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult: ...
    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult: ...
    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult: ...
    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult: ...
    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult: ...
    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult: ...
    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult: ...
    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult: ...
    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult: ...
    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult: ...
    def supervisor_logs(self, request: RuntimeLogsRequest) -> str: ...
    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult: ...
    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult: ...
    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult: ...
    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult: ...
    def techlead_service_map(self) -> TechLeadServiceMapResultView: ...
    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView: ...
    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView: ...
    def evaluate_automation_preflight(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView: ...


class InProcessRuntimeApiClient:
    def __init__(
        self,
        *,
        queue_admin: DefaultQueueAdminApplicationService | None = None,
        runtime_admin: DefaultRuntimeAdminApplicationService | None = None,
        runtime_install: DefaultRuntimeInstallApplicationService | None = None,
        runtime_report: DefaultRuntimeReportApplicationService | None = None,
        runtime_validation: DefaultRuntimeValidationApplicationService | None = None,
        automation_preflight: DefaultAutomationPreflightApplicationService | None = None,
        operator_commands: DefaultOperatorCommandApplicationService | None = None,
        producer_commands: DefaultProducerCommandApplicationService | None = None,
        authority_install: DefaultAuthorityInstallApplicationService | None = None,
        component_taxonomy: ComponentTaxonomyService | None = None,
    ) -> None:
        self._queue_admin = queue_admin or DefaultQueueAdminApplicationService()
        self._runtime_admin = runtime_admin or DefaultRuntimeAdminApplicationService()
        self._runtime_install = runtime_install or DefaultRuntimeInstallApplicationService()
        self._runtime_report = runtime_report or DefaultRuntimeReportApplicationService()
        self._runtime_validation = runtime_validation or DefaultRuntimeValidationApplicationService()
        self._automation_preflight = automation_preflight or DefaultAutomationPreflightApplicationService()
        self._operator_commands = operator_commands or build_default_operator_command_service(logger=_NullStructuredLogger())
        self._producer_commands = producer_commands or DefaultProducerCommandApplicationService()
        self._authority_install = authority_install or DefaultAuthorityInstallApplicationService()
        if component_taxonomy is None:
            from paa_core.application.services import DefaultComponentTaxonomyApplicationService

            self._component_taxonomy = DefaultComponentTaxonomyApplicationService()
        else:
            self._component_taxonomy = component_taxonomy

    def install_authority_package(self, request: AuthorityInstallRequest) -> AuthorityInstallResultView:
        return self._authority_install.install_package(request)

    def install_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult:
        return self._runtime_install.install_runtime(request)

    def update_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult:
        return self._runtime_install.update_runtime(request)

    def run_operator_command(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        return self._operator_commands.run_command(request)

    def supports_operator_command_family(self, command_family: str) -> bool:
        return self._operator_commands.supports_command_family(command_family)

    def list_realization_types(self, request: ListRealizationTypesRequest) -> ComponentTaxonomyOperationResult:
        return self._component_taxonomy.list_realization_types(request)

    def get_realization_type(self, request: GetRealizationTypeRequest) -> ComponentTaxonomyOperationResult:
        return self._component_taxonomy.get_realization_type(request)

    def list_element_type_realization_links(
        self, request: ListElementTypeRealizationLinksRequest
    ) -> ComponentTaxonomyOperationResult:
        return self._component_taxonomy.list_element_type_realization_links(request)

    def upsert_element_type_realization_link(
        self, request: UpsertElementTypeRealizationLinkRequest
    ) -> ComponentTaxonomyOperationResult:
        return self._component_taxonomy.upsert_element_type_realization_link(request)

    def upsert_realization_type(self, request: UpsertRealizationTypeRequest) -> ComponentTaxonomyOperationResult:
        return self._component_taxonomy.upsert_realization_type(request)

    def assemble_coder_brief(self, request: ProducerAssembleCoderBriefRequest) -> ProducerOperationResult:
        return self._producer_commands.assemble_coder_brief(request)

    def author_brief_targets(self, request: ProducerAuthorBriefTargetsRequest) -> ProducerOperationResult:
        return self._producer_commands.author_brief_targets(request)

    def derive_artifacts(self, request: ProducerDeriveArtifactsRequest) -> ProducerOperationResult:
        return self._producer_commands.derive_artifacts(request)

    def derive_design_package(self, request: ProducerDeriveDesignPackageRequest) -> ProducerOperationResult:
        return self._producer_commands.derive_design_package(request)

    def evaluate_derivation_readiness(
        self,
        request: ProducerEvaluateDerivationReadinessRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.evaluate_derivation_readiness(request)

    def derive_implementation_plan(
        self,
        request: ProducerDeriveImplementationPlanRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.derive_implementation_plan(request)

    def implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.implementation_plan_progress(request)

    def derive_next_activity_bundle(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.derive_next_activity_bundle(request)

    def reconcile_implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.reconcile_implementation_plan_progress(request)

    def set_implementation_plan_activity_state(
        self,
        request: ProducerSetImplementationPlanActivityStateRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.set_implementation_plan_activity_state(request)

    def review_coder_brief(self, request: ProducerReviewCoderBriefRequest) -> ProducerOperationResult:
        return self._producer_commands.review_coder_brief(request)

    def prepare_architect_packet(self, request: ProducerPrepareArchitectPacketRequest) -> ProducerOperationResult:
        return self._producer_commands.prepare_architect_packet(request)

    def materialize_readiness(self, request: ProducerMaterializeReadinessRequest) -> ProducerOperationResult:
        return self._producer_commands.materialize_readiness(request)

    def authority_command(self, request: ProducerAuthorityCommandRequest) -> ProducerOperationResult:
        return self._producer_commands.authority_command(request)

    def materialize_component_spec(
        self,
        request: ProducerMaterializeComponentSpecRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.materialize_component_spec(request)

    def publish_authority_package(self, request: ProducerPublishAuthorityPackageRequest) -> ProducerOperationResult:
        return self._producer_commands.publish_authority_package(request)

    def producer_smoke_test(self, request: ProducerSmokeTestRequest) -> ProducerOperationResult:
        return self._producer_commands.smoke_test(request)

    def load_issue_into_paa(self, request: ProducerLoadIssueRequest) -> ProducerOperationResult:
        return self._producer_commands.load_issue_into_paa(request)

    def materialize_verification_obligations(
        self,
        request: ProducerMaterializeVerificationObligationsRequest,
    ) -> ProducerOperationResult:
        return self._producer_commands.materialize_verification_obligations(request)

    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        return self._queue_admin.ensure_topology(request)

    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        return self._queue_admin.state_info(request)

    def check(self, request: QueueCheckRequest) -> QueueOperationResult:
        return self._queue_admin.check(request)

    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult:
        return self._queue_admin.purge(request)

    def validate(self, request: QueueValidateRequest) -> QueueOperationResult:
        return self._queue_admin.validate(request)

    def send(self, request: QueueSendRequest) -> QueueOperationResult:
        return self._queue_admin.send(request)

    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult:
        return self._queue_admin.claim_next(request)

    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult:
        return self._queue_admin.list_claims(request)

    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        return self._queue_admin.ack(request)

    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        return self._queue_admin.requeue(request)

    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        return self._queue_admin.validate_packet(request)

    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        return self._queue_admin.send_packet(request)

    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_supervisor(request)

    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        return self._runtime_admin.start_supervisor(request)

    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        return self._runtime_admin.stop_supervisor(request)

    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        return self._runtime_admin.supervisor_status(request)

    def supervisor_logs(self, request: RuntimeLogsRequest) -> str:
        return self._runtime_admin.supervisor_logs(request)

    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        return self._runtime_admin.restart_supervisor(request)

    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_techlead_host(request)

    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_dev_host(request)

    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_qa_host(request)

    def techlead_service_map(self) -> TechLeadServiceMapResultView:
        return self._runtime_report.techlead_service_map()

    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView:
        return self._runtime_validation.validate_runtime(request)

    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView:
        return self._runtime_validation.runtime_smoke(request)

    def evaluate_automation_preflight(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView:
        return self._automation_preflight.evaluate(request)


class HttpRuntimeApiClient:
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url.rstrip('/')

    def _get_json(self, path: str, *, params: dict[str, object] | None = None) -> dict[str, Any]:
        url = f'{self._base_url}{path}'
        if params:
            encoded = urlencode({key: str(value) for key, value in params.items() if value is not None})
            if encoded:
                url = f'{url}?{encoded}'
        with urlopen(url) as response:  # noqa: S310
            return json.loads(response.read().decode('utf-8'))

    def _get_json_response(self, path: str, *, params: dict[str, object] | None = None) -> tuple[int, dict[str, Any]]:
        url = f'{self._base_url}{path}'
        if params:
            encoded = urlencode({key: str(value) for key, value in params.items() if value is not None})
            if encoded:
                url = f'{url}?{encoded}'
        try:
            with urlopen(url) as response:  # noqa: S310
                return int(response.status), json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            body = exc.read().decode('utf-8')
            raw_payload = cast(dict[str, Any], json.loads(body) if body else {})
            detail = cast(dict[str, Any] | None, raw_payload.get('detail')) if isinstance(raw_payload, dict) else None
            return exc.code, detail or raw_payload

    def _post_json(self, path: str, payload: object) -> dict[str, Any]:
        body = json.dumps(_to_jsonable(payload)).encode('utf-8')
        request = Request(
            f'{self._base_url}{path}',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urlopen(request) as response:  # noqa: S310
            return json.loads(response.read().decode('utf-8'))

    def _post_json_response(self, path: str, payload: object) -> tuple[int, dict[str, Any]]:
        body = json.dumps(_to_jsonable(payload)).encode('utf-8')
        request = Request(
            f'{self._base_url}{path}',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urlopen(request) as response:  # noqa: S310
                return int(response.status), json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            body = exc.read().decode('utf-8')
            raw_payload = cast(dict[str, Any], json.loads(body) if body else {})
            detail = cast(dict[str, Any] | None, raw_payload.get('detail')) if isinstance(raw_payload, dict) else None
            return exc.code, detail or raw_payload

    def run_operator_command(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        payload = self._post_json('/runtime/operators/command', request)
        return _operator_command_result_from_payload(payload)

    def supports_operator_command_family(self, command_family: str) -> bool:
        payload = self._get_json(f'/runtime/operators/supports/{command_family}')
        return bool(payload.get('supported', False))

    def list_realization_types(self, request: ListRealizationTypesRequest) -> ComponentTaxonomyOperationResult:
        del request
        payload = self._get_json('/runtime/component-taxonomy/realization-types')
        return ComponentTaxonomyOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def get_realization_type(self, request: GetRealizationTypeRequest) -> ComponentTaxonomyOperationResult:
        status_code, payload = self._get_json_response(
            f'/runtime/component-taxonomy/realization-types/{request.realization_key}'
        )
        exit_code = 0 if status_code == 200 and payload.get('ok', True) else 1
        return ComponentTaxonomyOperationResult(payload=payload, exit_code=exit_code)

    def list_element_type_realization_links(
        self, request: ListElementTypeRealizationLinksRequest
    ) -> ComponentTaxonomyOperationResult:
        status_code, payload = self._get_json_response(
            '/runtime/component-taxonomy/realization-maps',
            params={'element_type_key': request.element_type_key},
        )
        exit_code = 0 if status_code == 200 and payload.get('ok', True) else 1
        return ComponentTaxonomyOperationResult(payload=payload, exit_code=exit_code)

    def upsert_element_type_realization_link(
        self, request: UpsertElementTypeRealizationLinkRequest
    ) -> ComponentTaxonomyOperationResult:
        status_code, payload = self._post_json_response('/runtime/component-taxonomy/realization-maps', request)
        exit_code = 0 if status_code == 200 and payload.get('ok', True) else 1
        return ComponentTaxonomyOperationResult(payload=payload, exit_code=exit_code)

    def upsert_realization_type(self, request: UpsertRealizationTypeRequest) -> ComponentTaxonomyOperationResult:
        payload = self._post_json('/runtime/component-taxonomy/realization-types', request)
        return ComponentTaxonomyOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def assemble_coder_brief(self, request: ProducerAssembleCoderBriefRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/assemble-coder-brief', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def author_brief_targets(self, request: ProducerAuthorBriefTargetsRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/author-brief-targets', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def derive_artifacts(self, request: ProducerDeriveArtifactsRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/derive-artifacts', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def derive_design_package(self, request: ProducerDeriveDesignPackageRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/derive-design-package', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def evaluate_derivation_readiness(
        self,
        request: ProducerEvaluateDerivationReadinessRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/evaluate-derivation-readiness', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def derive_implementation_plan(
        self,
        request: ProducerDeriveImplementationPlanRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/derive-implementation-plan', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/implementation-plan-progress', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def derive_next_activity_bundle(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/derive-next-activity-bundle', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def reconcile_implementation_plan_progress(
        self,
        request: ProducerImplementationPlanProgressRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/reconcile-implementation-plan-progress', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def set_implementation_plan_activity_state(
        self,
        request: ProducerSetImplementationPlanActivityStateRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/set-implementation-plan-activity-state', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def review_coder_brief(self, request: ProducerReviewCoderBriefRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/review-coder-brief', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def prepare_architect_packet(self, request: ProducerPrepareArchitectPacketRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/prepare-architect-packet', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def materialize_readiness(self, request: ProducerMaterializeReadinessRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/materialize-readiness', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def authority_command(self, request: ProducerAuthorityCommandRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/authority', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def materialize_component_spec(
        self,
        request: ProducerMaterializeComponentSpecRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/materialize-component-spec', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def publish_authority_package(self, request: ProducerPublishAuthorityPackageRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/publish-authority-package', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def producer_smoke_test(self, request: ProducerSmokeTestRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/smoke-test', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def load_issue_into_paa(self, request: ProducerLoadIssueRequest) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/load-issue-into-paa', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def materialize_verification_obligations(
        self,
        request: ProducerMaterializeVerificationObligationsRequest,
    ) -> ProducerOperationResult:
        payload = self._post_json('/runtime/producer/materialize-verification-obligations', request)
        return ProducerOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def install_authority_package(self, request: AuthorityInstallRequest) -> AuthorityInstallResultView:
        payload = self._post_json('/runtime/authority/install-package', request)
        return AuthorityInstallResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def install_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/ops/install-runtime', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def update_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/ops/update-runtime', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/ensure-topology', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        payload = self._get_json('/runtime/queues/state-info', params={'repo_root': request.repo_root})
        return QueueOperationResult(payload=payload, exit_code=0)

    def check(self, request: QueueCheckRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/check', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/purge', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def validate(self, request: QueueValidateRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/validate', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def send(self, request: QueueSendRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/send', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/claim-next', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/list-claims', request)
        return QueueOperationResult(payload=payload, exit_code=0)

    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/ack', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/requeue', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/validate-packet', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/send-packet', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/run', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/start', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/stop', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        payload = self._get_json('/runtime/supervisor/status', params={'repo_root': request.repo_root})
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def supervisor_logs(self, request: RuntimeLogsRequest) -> str:
        payload = self._get_json('/runtime/supervisor/logs', params={'repo_root': request.repo_root, 'lines': request.lines})
        return str(payload.get('output', ''))

    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/restart', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/hosts/techlead', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/hosts/dev', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/hosts/qa', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def techlead_service_map(self) -> TechLeadServiceMapResultView:
        payload = self._get_json('/runtime/reports/techlead-service-map')
        return TechLeadServiceMapResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView:
        payload = self._post_json('/runtime/status/validate', request)
        return RuntimeStatusResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView:
        payload = self._post_json('/runtime/status/smoke', request)
        return RuntimeStatusResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def evaluate_automation_preflight(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView:
        payload = self._post_json('/runtime/workflow/automation-preflight', request)
        return AutomationPreflightResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


def _operator_command_result_from_payload(payload: dict[str, Any]) -> OperatorCommandResult:
    command_payload = cast(dict[str, Any], payload['command'])
    failure_payload = cast(dict[str, Any] | None, payload.get('failure'))
    sections_payload = cast(list[dict[str, Any]], payload.get('sections', []))
    return OperatorCommandResult(
        command=OperatorCommand(
            command_family=str(command_payload['command_family']),
            command_name=str(command_payload['command_name']),
            subcommand_name=str(command_payload['subcommand_name']) if command_payload.get('subcommand_name') is not None else None,
        ),
        supported=bool(payload['supported']),
        success=bool(payload['success']),
        exit_code=int(payload['exit_code']),
        sections=tuple(_operator_output_section_from_payload(section) for section in sections_payload),
        failure=_operator_failure_from_payload(failure_payload),
        metadata=cast(dict[str, Any], payload.get('metadata', {})),
    )


def _operator_output_section_from_payload(payload: dict[str, Any]) -> OperatorOutputSection:
    messages_payload = cast(list[dict[str, Any]], payload.get('messages', []))
    tables_payload = cast(list[dict[str, Any]], payload.get('tables', []))
    return OperatorOutputSection(
        title=str(payload['title']),
        messages=tuple(
            OperatorOutputMessage(level=str(message['level']), text=str(message['text'])) for message in messages_payload
        ),
        tables=tuple(
            OperatorOutputTable(
                title=str(table['title']),
                columns=tuple(str(column) for column in cast(list[Any], table.get('columns', []))),
                rows=tuple(tuple(str(cell) for cell in cast(list[Any], row)) for row in cast(list[list[Any]], table.get('rows', []))),
            )
            for table in tables_payload
        ),
        data=cast(dict[str, Any], payload.get('data', {})),
    )


def _operator_failure_from_payload(payload: dict[str, Any] | None) -> OperatorFailure | None:
    if payload is None:
        return None
    return OperatorFailure(
        code=str(payload['code']),
        summary=str(payload['summary']),
        details=tuple(str(detail) for detail in cast(list[Any], payload.get('details', []))),
        blocking=bool(payload.get('blocking', True)),
        metadata=cast(dict[str, Any], payload.get('metadata', {})),
    )


__all__ = ['HttpRuntimeApiClient', 'InProcessRuntimeApiClient', 'RuntimeApiClient']
