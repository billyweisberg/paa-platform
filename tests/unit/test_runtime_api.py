from __future__ import annotations

import sys
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.api.runtime.app import build_runtime_api_app
from paa_core.api.runtime.dependencies import (
    get_authority_install_service,
    get_automation_preflight_service,
    get_component_taxonomy_service,
    get_methodology_execution_service,
    get_operator_command_service,
    get_producer_command_service,
    get_queue_admin_service,
    get_runtime_admin_service,
    get_runtime_dispatch_service,
    get_runtime_install_service,
    get_runtime_report_service,
    get_runtime_validation_service,
)
from paa_core.application.dto.authority import AuthorityInstallResultView
from paa_core.application.dto.component_taxonomy import ComponentTaxonomyOperationResult
from paa_core.application.dto.methodology_execution import MethodologyExecutionOperationResult
from paa_core.application.dto.queue import QueueOperationResult
from paa_core.application.dto.operator import (
    OperatorCommand,
    OperatorCommandResult,
    OperatorOutputMessage,
    OperatorOutputSection,
)
from paa_core.application.dto.producer import ProducerOperationResult
from paa_core.application.dto.runtime import RuntimeOperationResult
from paa_core.application.dto.status import RuntimeStatusResultView, TechLeadServiceMapResultView
from paa_core.application.dto.workflow import AutomationPreflightResultView


class _FakeQueueAdminService:
    def ensure_topology(self, request):
        return QueueOperationResult(payload={'ok': True, 'queue_action': 'ensure_topology', 'repo_root': str(request.repo_root)})

    def state_info(self, request):
        return QueueOperationResult(payload={'ok': True, 'queue_action': 'state_info', 'repo_root': str(request.repo_root)})

    def check(self, request):
        return QueueOperationResult(payload={'ok': True, 'queue': request.queue, 'preview': request.preview})

    def purge(self, request):
        return QueueOperationResult(payload={'ok': True, 'queue': request.queue})

    def validate(self, request):
        return QueueOperationResult(payload={'ok': True, 'message_file': str(request.message_file)})

    def send(self, request):
        return QueueOperationResult(payload={'ok': True, 'queue': request.queue, 'message_file': str(request.message_file)})

    def claim_next(self, request):
        return QueueOperationResult(payload={'ok': True, 'queue': request.queue, 'claimed_by': request.claimed_by})

    def list_claims(self, request):
        return QueueOperationResult(payload={'claims': [], 'queue': request.queue, 'status': request.status})

    def ack(self, request):
        return QueueOperationResult(payload={'ok': True, 'claim_id': request.claim_id})

    def requeue(self, request):
        return QueueOperationResult(payload={'ok': True, 'claim_id': request.claim_id})

    def validate_packet(self, request):
        return QueueOperationResult(payload={'ok': True, 'message_file': str(request.message_file)})

    def send_packet(self, request):
        return QueueOperationResult(payload={'ok': True, 'message_file': str(request.message_file)})


class _FakeRuntimeAdminService:
    def run_supervisor(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'action': 'run', 'repo_root': str(request.repo_root)})

    def start_supervisor(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'action': 'start', 'repo_root': str(request.repo_root)})

    def stop_supervisor(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'action': 'stop', 'repo_root': str(request.repo_root)})

    def supervisor_status(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'running': True, 'repo_root': str(request.repo_root)})

    def supervisor_logs(self, request):
        return 'runtime logs here'

    def restart_supervisor(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'action': 'restart', 'repo_root': str(request.repo_root)})

    def run_techlead_host(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'host': 'techlead', 'host_name': request.host_name})

    def run_dev_host(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'host': 'dev', 'host_name': request.host_name})

    def run_qa_host(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'host': 'qa', 'host_name': request.host_name})


class _FakeRuntimeDispatchService:
    def dispatch_packet(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'dispatch': 'generic', 'message_file': str(request.message_file)})

    def dispatch_techlead_packet(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'dispatch': 'techlead', 'message_file': str(request.message_file)})


class _FakeRuntimeValidationService:
    def validate_runtime(self, request):
        return RuntimeStatusResultView(payload={'ok': True, 'branch': 'main', 'repo_root': str(request.repo_root)})

    def runtime_smoke(self, request):
        return RuntimeStatusResultView(payload={'ok': True, 'repo_root': str(request.repo_root), 'expected_branch': request.expected_branch})


class _FakeRuntimeReportService:
    def techlead_service_map(self):
        return TechLeadServiceMapResultView(payload={'techlead_shell_status': 'retired', 'extracted_service_count': 7})


class _FakeAutomationPreflightService:
    def evaluate(self, request):
        return AutomationPreflightResultView(
            payload={'ok': True, 'project_slug': request.project_slug, 'target_role': request.target_role}
        )


class _FakeOperatorCommandService:
    def run_command(self, request):
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Operator Command',
                    messages=(OperatorOutputMessage(level='info', text=f"ran {request.command.command_family}:{request.command.command_name}"),),
                    data={'arguments': request.arguments},
                ),
            ),
        )

    def supports_command_family(self, command_family: str) -> bool:
        return command_family in {'component', 'plan', 'status', 'report', 'role', 'agent', 'queue', 'worker'}


class _FakeAuthorityInstallService:
    def install_package(self, request):
        return AuthorityInstallResultView(
            payload={'ok': True, 'repo_root': str(request.repo_root), 'package_root': str(request.package_root)},
            exit_code=0,
        )


class _FakeRuntimeInstallService:
    def install_runtime(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'action': 'install', 'project_pack': request.project_pack})

    def update_runtime(self, request):
        return RuntimeOperationResult(payload={'ok': True, 'action': 'update', 'project_pack': request.project_pack})


class _FakeProducerCommandService:
    def derive_artifacts(self, request):
        return ProducerOperationResult(payload={'ok': True, 'command': 'derive-artifacts', 'repo_root': str(request.repo_root)})

    def publish_authority_package(self, request):
        return ProducerOperationResult(payload={'ok': True, 'command': 'publish-authority-package', 'project_config': str(request.project_config)})

    def smoke_test(self, request):
        return ProducerOperationResult(payload={'ok': True, 'command': 'smoke-test', 'repo_root': str(request.repo_root)})

    def load_issue_into_paa(self, request):
        return ProducerOperationResult(payload={'ok': True, 'command': 'load-issue-into-paa', 'issue_number': request.issue_number})

    def materialize_verification_obligations(self, request):
        return ProducerOperationResult(payload={'ok': True, 'command': 'materialize-verification-obligations', 'issue_number': request.issue_number})


class _FakeComponentTaxonomyService:
    def list_realization_types(self, request):
        del request
        items = [
            {
                'component_element_realization_type_id': '10',
                'realization_key': 'service_interface',
                'label': 'Service Interface',
                'category': 'code_artifact',
                'description': 'Contract surface',
                'is_brief_targetable': True,
                'is_multi_instance': False,
                'sort_order': 10,
                'metadata': {'language': 'python'},
                'is_default_for_element_type': False,
                'element_type_sort_order': 0,
            },
            {
                'component_element_realization_type_id': '11',
                'realization_key': 'typed_service_class',
                'label': 'Typed Service Class',
                'category': 'python_artifact',
                'description': None,
                'is_brief_targetable': True,
                'is_multi_instance': True,
                'sort_order': 20,
                'metadata': {},
                'is_default_for_element_type': False,
                'element_type_sort_order': 0,
            },
        ]
        return ComponentTaxonomyOperationResult(payload={'ok': True, 'items': items, 'count': len(items)})

    def get_realization_type(self, request):
        if request.realization_key == 'missing_type':
            return ComponentTaxonomyOperationResult(
                payload={'ok': False, 'code': 'realization_type_not_found', 'realization_key': request.realization_key},
                exit_code=1,
            )
        return ComponentTaxonomyOperationResult(
            payload={
                'ok': True,
                'item': {
                    'component_element_realization_type_id': '10',
                    'realization_key': request.realization_key,
                    'label': 'Service Interface',
                    'category': 'code_artifact',
                    'description': 'Contract surface',
                    'is_brief_targetable': True,
                    'is_multi_instance': False,
                    'sort_order': 10,
                    'metadata': {'language': 'python'},
                    'is_default_for_element_type': False,
                    'element_type_sort_order': 0,
                },
            }
        )

    def upsert_realization_type(self, request):
        return ComponentTaxonomyOperationResult(
            payload={'ok': True, 'realization_key': request.realization_key, 'action': 'upserted'}
        )

    def list_element_type_realization_links(self, request):
        if request.element_type_key == 'missing_element_type':
            return ComponentTaxonomyOperationResult(
                payload={'ok': False, 'code': 'element_type_not_found', 'element_type_key': request.element_type_key},
                exit_code=1,
            )
        items = [
            {
                'component_element_type_realization_type_id': '30',
                'component_element_type_id': '20',
                'component_element_realization_type_id': '10',
                'element_type_key': request.element_type_key,
                'realization_key': 'service_interface',
                'realization_label': 'Service Interface',
                'realization_category': 'code_artifact',
                'is_default': True,
                'sort_order': 10,
                'metadata': {'language': 'python'},
            },
            {
                'component_element_type_realization_type_id': '31',
                'component_element_type_id': '20',
                'component_element_realization_type_id': '11',
                'element_type_key': request.element_type_key,
                'realization_key': 'typed_service_class',
                'realization_label': 'Typed Service Class',
                'realization_category': 'python_artifact',
                'is_default': False,
                'sort_order': 20,
                'metadata': {},
            },
        ]
        return ComponentTaxonomyOperationResult(
            payload={
                'ok': True,
                'element_type': {
                    'component_element_type_id': '20',
                    'element_key': request.element_type_key,
                    'label': 'Interfaces',
                    'category': 'contract',
                    'description': 'Contract surfaces',
                    'is_brief_targetable': True,
                    'is_multi_instance': True,
                    'sort_order': 5,
                    'metadata': {'scope': 'app'},
                },
                'items': items,
                'count': len(items),
            }
        )

    def upsert_element_type_realization_link(self, request):
        if request.element_type_key == 'missing_element_type':
            return ComponentTaxonomyOperationResult(
                payload={'ok': False, 'code': 'element_type_not_found', 'element_type_key': request.element_type_key},
                exit_code=1,
            )
        if request.realization_key == 'missing_realization_type':
            return ComponentTaxonomyOperationResult(
                payload={'ok': False, 'code': 'realization_type_not_found', 'realization_key': request.realization_key},
                exit_code=1,
            )
        return ComponentTaxonomyOperationResult(
            payload={
                'ok': True,
                'element_type_key': request.element_type_key,
                'realization_key': request.realization_key,
                'action': 'upserted',
            }
        )


class _FakeMethodologyExecutionService:
    def get_status(self, request):
        if request.methodology_execution_id == 'missing-exec' or request.project_id == 'missing-project':
            return MethodologyExecutionOperationResult(
                payload={
                    'ok': False,
                    'code': 'methodology_execution_not_found',
                    'methodology_execution_id': request.methodology_execution_id,
                    'project_id': request.project_id,
                    'work_item_id': request.work_item_id,
                    'component_id': request.component_id,
                },
                exit_code=1,
            )
        if request.methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return MethodologyExecutionOperationResult(payload={'ok': False, 'code': 'missing_methodology_identity'}, exit_code=1)
        return MethodologyExecutionOperationResult(
            payload={
                'ok': True,
                'item': {
                    'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                    'lane': 'component_realization',
                    'stage': 'slice_execution',
                    'step': 'reconcile_component_plan_progress',
                    'status': 'active',
                    'current_owner_role': 'techlead',
                    'next_action_key': 'component-progress-reconciled',
                    'blocked_reason': None,
                    'component_id': request.component_id,
                    'design_package_id': None,
                    'implementation_plan_id': 'plan-1',
                    'coder_run_brief_id': None,
                    'packet_id': None,
                    'workflow_state_id': 'wf-1',
                    'active_authority_ref': None,
                    'active_artifact_ref': None,
                    'binding_refs': [],
                    'summary_text': 'Current methodology state.',
                    'metadata': {},
                },
            }
        )

    def get_next_action(self, request):
        if request.methodology_execution_id == 'missing-exec' or request.project_id == 'missing-project':
            return MethodologyExecutionOperationResult(
                payload={
                    'ok': False,
                    'code': 'methodology_execution_not_found',
                    'methodology_execution_id': request.methodology_execution_id,
                    'project_id': request.project_id,
                    'work_item_id': request.work_item_id,
                    'component_id': request.component_id,
                },
                exit_code=1,
            )
        if request.methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return MethodologyExecutionOperationResult(payload={'ok': False, 'code': 'missing_methodology_identity'}, exit_code=1)
        return MethodologyExecutionOperationResult(
            payload={
                'ok': True,
                'item': {
                    'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                    'recommended_next_action_key': 'component-progress-reconciled',
                    'recommended_owner_role': 'techlead',
                    'lane': 'component_realization',
                    'stage': 'slice_execution',
                    'step': 'reconcile_component_plan_progress',
                    'prerequisite_summary': 'Ready to reconcile.',
                    'blocked_reason': None,
                    'component_id': request.component_id,
                    'implementation_plan_id': 'plan-1',
                    'packet_id': None,
                    'metadata': {},
                },
            }
        )

    def explain(self, request):
        if request.methodology_execution_id == 'missing-exec' or request.project_id == 'missing-project':
            return MethodologyExecutionOperationResult(
                payload={
                    'ok': False,
                    'code': 'methodology_execution_not_found',
                    'methodology_execution_id': request.methodology_execution_id,
                    'project_id': request.project_id,
                    'work_item_id': request.work_item_id,
                    'component_id': request.component_id,
                },
                exit_code=1,
            )
        if request.methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return MethodologyExecutionOperationResult(payload={'ok': False, 'code': 'missing_methodology_identity'}, exit_code=1)
        return MethodologyExecutionOperationResult(
            payload={
                'ok': True,
                'item': {
                    'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                    'lane': 'component_realization',
                    'stage': 'slice_execution',
                    'step': 'reconcile_component_plan_progress',
                    'status': 'active',
                    'current_owner_role': 'techlead',
                    'explanation_summary': 'Waiting on progress reconciliation.',
                    'transition_context': {'transition_key': 'component-progress-reconciled'},
                    'binding_refs': [],
                    'blocked_reason': None,
                    'metadata': {},
                },
            }
        )

    def apply_transition(self, request):
        if request.methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return MethodologyExecutionOperationResult(payload={'ok': False, 'code': 'missing_methodology_identity'}, exit_code=1)
        if request.methodology_execution_id == 'missing-exec' or request.project_id == 'missing-project':
            return MethodologyExecutionOperationResult(
                payload={
                    'ok': False,
                    'code': 'methodology_execution_not_found',
                    'methodology_execution_id': request.methodology_execution_id,
                    'project_id': request.project_id,
                    'work_item_id': request.work_item_id,
                    'component_id': request.component_id,
                },
                exit_code=1,
            )
        if request.transition_key == 'blocked-transition':
            return MethodologyExecutionOperationResult(
                payload={
                    'ok': False,
                    'code': 'unsupported_transition_key',
                    'details': 'Transition is not supported in this slice.',
                    'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                    'current_state': {
                        'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                        'lane': 'component_realization',
                        'stage': 'slice_execution',
                        'step': 'reconcile_component_plan_progress',
                        'status': 'active',
                        'current_owner_role': 'techlead',
                        'next_action_key': 'component-progress-reconciled',
                        'blocked_reason': None,
                        'component_id': request.component_id,
                        'design_package_id': None,
                        'implementation_plan_id': 'plan-1',
                        'coder_run_brief_id': None,
                        'packet_id': None,
                        'workflow_state_id': 'wf-1',
                        'active_authority_ref': None,
                        'active_artifact_ref': None,
                        'binding_refs': [],
                        'summary_text': 'Current methodology state.',
                        'metadata': {},
                    },
                },
                exit_code=1,
            )
        return MethodologyExecutionOperationResult(
            payload={
                'ok': True,
                'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                'current_state': {
                    'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                    'lane': 'component_realization',
                    'stage': 'slice_execution',
                    'step': 'derive_next_activity_bundle',
                    'status': 'ready',
                    'current_owner_role': 'producer',
                    'next_action_key': 'derive-next-activity-bundle',
                    'blocked_reason': None,
                    'component_id': request.component_id,
                    'design_package_id': None,
                    'implementation_plan_id': 'plan-1',
                    'coder_run_brief_id': None,
                    'packet_id': None,
                    'workflow_state_id': 'wf-1',
                    'active_authority_ref': None,
                    'active_artifact_ref': None,
                    'binding_refs': [],
                    'summary_text': 'Transition applied.',
                    'metadata': {},
                },
                'transition': {
                    'transition_key': request.transition_key,
                    'from_step': 'reconcile_component_plan_progress',
                    'to_step': 'derive_next_activity_bundle',
                    'from_status': 'active',
                    'to_status': 'ready',
                    'event_type': 'methodology_transition',
                    'notes': request.notes,
                    'metadata': request.metadata or {},
                },
                'binding_update_applied': bool(request.binding_entries),
            }
        )

    def evaluate_preflight(self, request):
        if request.methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return MethodologyExecutionOperationResult(payload={'ok': False, 'code': 'missing_methodology_identity'}, exit_code=1)
        blocked = request.command_name == 'blocked'
        return MethodologyExecutionOperationResult(
            payload={
                'ok': not blocked,
                'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                'outcome': {
                    'allowed': not blocked,
                    'classification': 'blocked' if blocked else 'allowed',
                    'recommended_command_family': request.command_family,
                    'recommended_command_name': request.command_name,
                    'message': 'blocked' if blocked else 'allowed',
                    'metadata': {},
                },
                'reason': 'blocked_state' if blocked else None,
                'details': 'Current methodology state blocks this command.' if blocked else None,
                'status_projection': {
                    'methodology_execution_id': request.methodology_execution_id or 'exec-1',
                    'lane': 'component_realization',
                    'stage': 'slice_execution',
                    'step': 'reconcile_component_plan_progress',
                    'status': 'active',
                    'current_owner_role': 'techlead',
                    'next_action_key': 'component-progress-reconciled',
                    'blocked_reason': None,
                    'component_id': request.component_id,
                    'design_package_id': None,
                    'implementation_plan_id': 'plan-1',
                    'coder_run_brief_id': None,
                    'packet_id': None,
                    'workflow_state_id': 'wf-1',
                    'active_authority_ref': None,
                    'active_artifact_ref': None,
                    'binding_refs': [],
                    'summary_text': 'Current methodology state.',
                    'metadata': {},
                },
            },
            exit_code=1 if blocked else 0,
        )


class RuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = build_runtime_api_app()
        self.app.dependency_overrides[get_authority_install_service] = lambda: _FakeAuthorityInstallService()
        self.app.dependency_overrides[get_component_taxonomy_service] = lambda: _FakeComponentTaxonomyService()
        self.app.dependency_overrides[get_methodology_execution_service] = lambda: _FakeMethodologyExecutionService()
        self.app.dependency_overrides[get_queue_admin_service] = lambda: _FakeQueueAdminService()
        self.app.dependency_overrides[get_runtime_admin_service] = lambda: _FakeRuntimeAdminService()
        self.app.dependency_overrides[get_runtime_dispatch_service] = lambda: _FakeRuntimeDispatchService()
        self.app.dependency_overrides[get_runtime_install_service] = lambda: _FakeRuntimeInstallService()
        self.app.dependency_overrides[get_runtime_validation_service] = lambda: _FakeRuntimeValidationService()
        self.app.dependency_overrides[get_runtime_report_service] = lambda: _FakeRuntimeReportService()
        self.app.dependency_overrides[get_automation_preflight_service] = lambda: _FakeAutomationPreflightService()
        self.app.dependency_overrides[get_operator_command_service] = lambda: _FakeOperatorCommandService()
        self.app.dependency_overrides[get_producer_command_service] = lambda: _FakeProducerCommandService()
        self.client = TestClient(self.app)

    def test_healthz(self) -> None:
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['service'], 'paa-runtime-api')

    def test_supervisor_start(self) -> None:
        response = self.client.post('/runtime/supervisor/start', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'start')

    def test_run_techlead_host(self) -> None:
        response = self.client.post(
            '/runtime/hosts/techlead',
            json={'repo_root': str(ROOT), 'actor_name': 'TechLead Agent', 'host_name': 'techlead-runtime-host'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['host'], 'techlead')

    def test_queue_ensure_topology(self) -> None:
        response = self.client.post('/runtime/queues/ensure-topology', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['queue_action'], 'ensure_topology')

    def test_runtime_validate(self) -> None:
        response = self.client.post('/runtime/status/validate', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_authority_install_package(self) -> None:
        response = self.client.post(
            '/runtime/authority/install-package',
            json={'repo_root': str(ROOT), 'package_root': str(ROOT / 'package')},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_component_taxonomy_list_realization_types(self) -> None:
        response = self.client.get('/runtime/component-taxonomy/realization-types')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['count'], 2)
        self.assertEqual(response.json()['items'][0]['realization_key'], 'service_interface')

    def test_component_taxonomy_get_realization_type(self) -> None:
        response = self.client.get('/runtime/component-taxonomy/realization-types/service_interface')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['realization_key'], 'service_interface')

    def test_component_taxonomy_get_realization_type_missing_returns_404(self) -> None:
        response = self.client.get('/runtime/component-taxonomy/realization-types/missing_type')
        self.assertEqual(response.status_code, 404)
        detail = response.json()['detail']
        self.assertFalse(detail['ok'])
        self.assertEqual(detail['code'], 'realization_type_not_found')
        self.assertEqual(detail['realization_key'], 'missing_type')

    def test_component_taxonomy_upsert_realization_type(self) -> None:
        response = self.client.post(
            '/runtime/component-taxonomy/realization-types',
            json={
                'realization_key': 'module_operation_surface',
                'label': 'Module Operation Surface',
                'category': 'python_artifact',
                'description': 'Function-style module surface',
                'is_brief_targetable': True,
                'is_multi_instance': False,
                'sort_order': 30,
                'metadata': {'language': 'python'},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['realization_key'], 'module_operation_surface')
        self.assertEqual(response.json()['action'], 'upserted')

    def test_component_taxonomy_list_realization_maps(self) -> None:
        response = self.client.get('/runtime/component-taxonomy/realization-maps', params={'element_type_key': 'interfaces'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['element_type']['element_key'], 'interfaces')
        self.assertEqual(response.json()['count'], 2)
        self.assertEqual(response.json()['items'][0]['realization_key'], 'service_interface')

    def test_component_taxonomy_list_realization_maps_missing_returns_404(self) -> None:
        response = self.client.get(
            '/runtime/component-taxonomy/realization-maps', params={'element_type_key': 'missing_element_type'}
        )
        self.assertEqual(response.status_code, 404)
        detail = response.json()['detail']
        self.assertFalse(detail['ok'])
        self.assertEqual(detail['code'], 'element_type_not_found')
        self.assertEqual(detail['element_type_key'], 'missing_element_type')

    def test_component_taxonomy_upsert_realization_map(self) -> None:
        response = self.client.post(
            '/runtime/component-taxonomy/realization-maps',
            json={
                'element_type_key': 'interfaces',
                'realization_key': 'typed_service_class',
                'is_default': False,
                'sort_order': 25,
                'metadata': {'language': 'python'},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['element_type_key'], 'interfaces')
        self.assertEqual(response.json()['realization_key'], 'typed_service_class')
        self.assertEqual(response.json()['action'], 'upserted')

    def test_component_taxonomy_upsert_realization_map_missing_element_type_returns_404(self) -> None:
        response = self.client.post(
            '/runtime/component-taxonomy/realization-maps',
            json={'element_type_key': 'missing_element_type', 'realization_key': 'typed_service_class'},
        )
        self.assertEqual(response.status_code, 404)
        detail = response.json()['detail']
        self.assertFalse(detail['ok'])
        self.assertEqual(detail['code'], 'element_type_not_found')

    def test_component_taxonomy_upsert_realization_map_missing_realization_type_returns_404(self) -> None:
        response = self.client.post(
            '/runtime/component-taxonomy/realization-maps',
            json={'element_type_key': 'interfaces', 'realization_key': 'missing_realization_type'},
        )
        self.assertEqual(response.status_code, 404)
        detail = response.json()['detail']
        self.assertFalse(detail['ok'])
        self.assertEqual(detail['code'], 'realization_type_not_found')
        self.assertEqual(detail['realization_key'], 'missing_realization_type')

    def test_methodology_execution_status_by_id(self) -> None:
        response = self.client.get('/runtime/methodology-execution/status', params={'methodology_execution_id': 'exec-1'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['methodology_execution_id'], 'exec-1')

    def test_methodology_execution_status_by_anchors(self) -> None:
        response = self.client.get(
            '/runtime/methodology-execution/status',
            params={'project_id': 'proj-1', 'work_item_id': 'work-1', 'component_id': 'component-1'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['component_id'], 'component-1')

    def test_methodology_execution_status_missing_identity_returns_400(self) -> None:
        response = self.client.get('/runtime/methodology-execution/status')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail']['code'], 'missing_methodology_identity')

    def test_methodology_execution_status_missing_returns_404(self) -> None:
        response = self.client.get('/runtime/methodology-execution/status', params={'methodology_execution_id': 'missing-exec'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail']['code'], 'methodology_execution_not_found')

    def test_methodology_execution_next_by_id(self) -> None:
        response = self.client.get('/runtime/methodology-execution/next', params={'methodology_execution_id': 'exec-1'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['recommended_next_action_key'], 'component-progress-reconciled')

    def test_methodology_execution_next_by_anchors(self) -> None:
        response = self.client.get(
            '/runtime/methodology-execution/next',
            params={'project_id': 'proj-1', 'work_item_id': 'work-1', 'component_id': 'component-1'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['component_id'], 'component-1')

    def test_methodology_execution_next_missing_returns_404(self) -> None:
        response = self.client.get('/runtime/methodology-execution/next', params={'methodology_execution_id': 'missing-exec'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail']['code'], 'methodology_execution_not_found')

    def test_methodology_execution_explain_by_id(self) -> None:
        response = self.client.get('/runtime/methodology-execution/explain', params={'methodology_execution_id': 'exec-1'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['methodology_execution_id'], 'exec-1')

    def test_methodology_execution_explain_by_anchors(self) -> None:
        response = self.client.get(
            '/runtime/methodology-execution/explain',
            params={'project_id': 'proj-1', 'work_item_id': 'work-1', 'component_id': 'component-1'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['item']['current_owner_role'], 'techlead')

    def test_methodology_execution_explain_missing_returns_404(self) -> None:
        response = self.client.get('/runtime/methodology-execution/explain', params={'methodology_execution_id': 'missing-exec'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail']['code'], 'methodology_execution_not_found')

    def test_methodology_execution_apply_transition(self) -> None:
        response = self.client.post(
            '/runtime/methodology-execution/transitions',
            json={
                'methodology_execution_id': 'exec-1',
                'transition_key': 'component-progress-reconciled',
                'notes': 'advance state',
                'binding_entries': [
                    {
                        'binding_kind': 'implementation_plan',
                        'bound_record_id': 'plan-1',
                        'is_primary': True,
                        'metadata': {'source': 'test'},
                    }
                ],
                'metadata': {'proof': 'api'},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['transition']['transition_key'], 'component-progress-reconciled')
        self.assertTrue(response.json()['binding_update_applied'])

    def test_methodology_execution_apply_transition_missing_identity_returns_400(self) -> None:
        response = self.client.post('/runtime/methodology-execution/transitions', json={'transition_key': 'component-progress-reconciled'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail']['code'], 'missing_methodology_identity')

    def test_methodology_execution_apply_transition_missing_returns_404(self) -> None:
        response = self.client.post(
            '/runtime/methodology-execution/transitions',
            json={'methodology_execution_id': 'missing-exec', 'transition_key': 'component-progress-reconciled'},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail']['code'], 'methodology_execution_not_found')

    def test_methodology_execution_apply_transition_blocked_returns_409(self) -> None:
        response = self.client.post(
            '/runtime/methodology-execution/transitions',
            json={'methodology_execution_id': 'exec-1', 'transition_key': 'blocked-transition'},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['detail']['code'], 'unsupported_transition_key')

    def test_methodology_execution_preflight_allowed_returns_200(self) -> None:
        response = self.client.post(
            '/runtime/methodology-execution/preflight',
            json={'methodology_execution_id': 'exec-1', 'command_family': 'component', 'command_name': 'next'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['outcome']['classification'], 'allowed')

    def test_methodology_execution_preflight_blocked_returns_200(self) -> None:
        response = self.client.post(
            '/runtime/methodology-execution/preflight',
            json={'methodology_execution_id': 'exec-1', 'command_family': 'component', 'command_name': 'blocked'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(response.json()['reason'], 'blocked_state')

    def test_methodology_execution_preflight_missing_identity_returns_400(self) -> None:
        response = self.client.post(
            '/runtime/methodology-execution/preflight',
            json={'command_family': 'component', 'command_name': 'next'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail']['code'], 'missing_methodology_identity')

    def test_install_runtime(self) -> None:
        response = self.client.post('/runtime/ops/install-runtime', json={'repo_root': str(ROOT), 'project_pack': 'fractal-core'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'install')

    def test_producer_derive_artifacts(self) -> None:
        response = self.client.post('/runtime/producer/derive-artifacts', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['command'], 'derive-artifacts')

    def test_producer_load_issue_into_paa(self) -> None:
        response = self.client.post(
            '/runtime/producer/load-issue-into-paa',
            json={'repo_root': str(ROOT), 'project_config': str(ROOT / 'project.json'), 'issue_number': 12},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['issue_number'], 12)

    def test_update_runtime(self) -> None:
        response = self.client.post('/runtime/ops/update-runtime', json={'repo_root': str(ROOT), 'project_pack': 'fractal-core'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'update')

    def test_runtime_report(self) -> None:
        response = self.client.get('/runtime/reports/techlead-service-map')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['extracted_service_count'], 7)

    def test_dispatch_runtime_packet(self) -> None:
        response = self.client.post(
            '/runtime/packets/dispatch',
            json={'repo_root': str(ROOT), 'message_file': str(ROOT / 'message.json')},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['dispatch'], 'generic')

    def test_dispatch_techlead_runtime_packet(self) -> None:
        response = self.client.post(
            '/runtime/packets/dispatch-techlead',
            json={'repo_root': str(ROOT), 'message_file': str(ROOT / 'message.json')},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['dispatch'], 'techlead')

    def test_automation_preflight(self) -> None:
        response = self.client.post(
            '/runtime/workflow/automation-preflight',
            json={'repo_root': str(ROOT), 'project_slug': 'paa-platform', 'target_role': 'TechLead'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['target_role'], 'TechLead')

    def test_operator_command(self) -> None:
        response = self.client.post(
            '/runtime/operators/command',
            json={
                'command': {'command_family': 'status', 'command_name': 'inspect', 'subcommand_name': None},
                'invocation_context': {'repo_root': str(ROOT), 'output_mode': 'table', 'dry_run': False, 'strict_mode': True, 'metadata': {}},
                'arguments': {'methodology_execution_id': 'exec-1'},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['sections'][0]['title'], 'Operator Command')

    def test_operator_supports_family(self) -> None:
        response = self.client.get('/runtime/operators/supports/status')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['supported'])


if __name__ == '__main__':
    unittest.main()
