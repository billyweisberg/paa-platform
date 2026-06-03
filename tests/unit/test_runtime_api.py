from __future__ import annotations

import sys
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.api.runtime.app import build_runtime_api_app
from paa_core.api.runtime.dependencies import (
    get_automation_preflight_service,
    get_queue_admin_service,
    get_runtime_admin_service,
    get_runtime_report_service,
    get_runtime_validation_service,
)
from paa_core.application.dto.queue import QueueOperationResult
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


class RuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = build_runtime_api_app()
        self.app.dependency_overrides[get_queue_admin_service] = lambda: _FakeQueueAdminService()
        self.app.dependency_overrides[get_runtime_admin_service] = lambda: _FakeRuntimeAdminService()
        self.app.dependency_overrides[get_runtime_validation_service] = lambda: _FakeRuntimeValidationService()
        self.app.dependency_overrides[get_runtime_report_service] = lambda: _FakeRuntimeReportService()
        self.app.dependency_overrides[get_automation_preflight_service] = lambda: _FakeAutomationPreflightService()
        self.client = TestClient(self.app)

    def test_healthz(self) -> None:
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['service'], 'paa-runtime-api')

    def test_supervisor_start(self) -> None:
        response = self.client.post('/runtime/supervisor/start', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'start')

    def test_queue_ensure_topology(self) -> None:
        response = self.client.post('/runtime/queues/ensure-topology', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['queue_action'], 'ensure_topology')

    def test_runtime_validate(self) -> None:
        response = self.client.post('/runtime/status/validate', json={'repo_root': str(ROOT)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_runtime_report(self) -> None:
        response = self.client.get('/runtime/reports/techlead-service-map')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['extracted_service_count'], 7)

    def test_automation_preflight(self) -> None:
        response = self.client.post(
            '/runtime/workflow/automation-preflight',
            json={'repo_root': str(ROOT), 'project_slug': 'paa-platform', 'target_role': 'TechLead'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['target_role'], 'TechLead')


if __name__ == '__main__':
    unittest.main()
