from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection
from paa_core.services.techlead_acceptance_decision.models import (
    TechLeadAcceptanceDecisionResult,
    TechLeadAcceptanceDecisionSummary,
)
from paa_core.services.techlead_assignment_decision.models import (
    TechLeadAssignmentDecisionResult,
    TechLeadAssignmentDecisionSummary,
)
from paa_core.services.techlead_worker import (
    DefaultTechLeadWorkerService,
    TECHLEAD_WORKER_SERVICE_METADATA,
    TechLeadWorkerRequest,
)
from paa_core.services.techlead_worker.contracts import TechLeadWorkerService
from paa_core.services.techlead_worker_review_routing import (
    TechLeadWorkerReviewRoutingResult,
    TechLeadWorkerReviewRoutingSummary,
)


class _FakeProjectionService:
    def __init__(self, status_projection: MethodologyExecutionStatusProjection) -> None:
        self.status_projection = status_projection
        self.requested_execution_ids: list[str] = []

    def get_status_projection(self, methodology_execution_id: str) -> MethodologyExecutionStatusProjection:
        self.requested_execution_ids.append(methodology_execution_id)
        return self.status_projection


class _FakeWorkerReviewRoutingService:
    def __init__(self, routing_result: TechLeadWorkerReviewRoutingResult) -> None:
        self.routing_result = routing_result
        self.requests: list[object] = []

    def derive_worker_review_routing(self, request: object) -> TechLeadWorkerReviewRoutingResult:
        self.requests.append(request)
        return self.routing_result


class _FakeAcceptanceDecisionService:
    def __init__(self, result: TechLeadAcceptanceDecisionResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def derive_acceptance_decision(self, request: object) -> TechLeadAcceptanceDecisionResult:
        self.requests.append(request)
        return self.result


class _FakeAssignmentDecisionService:
    def __init__(self, result: TechLeadAssignmentDecisionResult) -> None:
        self.result = result
        self.requests: list[object] = []

    def derive_assignment_decision(self, request: object) -> TechLeadAssignmentDecisionResult:
        self.requests.append(request)
        return self.result


class TechLeadWorkerServiceTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(TECHLEAD_WORKER_SERVICE_METADATA.name, 'TechLeadWorkerService')
        self.assertEqual(TECHLEAD_WORKER_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_service_methods(self) -> None:
        self.assertTrue(hasattr(TechLeadWorkerService, 'handle_packet'))
        self.assertTrue(hasattr(TechLeadWorkerService, 'supports_packet_schema_type'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(TechLeadWorkerService, 'methodology_execution_repository'))
        self.assertTrue(hasattr(TechLeadWorkerService, 'methodology_execution_state_service'))
        self.assertTrue(hasattr(TechLeadWorkerService, 'methodology_execution_projection_service'))
        self.assertTrue(hasattr(TechLeadWorkerService, 'methodology_execution_preflight_service'))
        self.assertTrue(hasattr(TechLeadWorkerService, 'techlead_worker_review_routing_service'))
        self.assertTrue(hasattr(TechLeadWorkerService, 'logger'))

    def test_handle_packet_supports_worker_result_packet_dry_run(self) -> None:
        projection = MethodologyExecutionStatusProjection(
            methodology_execution_id='exec-123',
            lane='component_realization',
            stage='slice_execution',
            step='techlead_worker_review_pending',
            status='active',
            current_owner_role='TechLead',
            next_action_key='review-worker-result',
            blocked_reason=None,
            component_id='component-123',
            design_package_id=None,
            implementation_plan_id='plan-123',
            coder_run_brief_id=None,
            packet_id='packet-123',
            workflow_state_id='workflow-123',
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=('implementation_plan:plan-123',),
            summary_text='TechLead is reviewing a worker result.',
        )
        routing_result = TechLeadWorkerReviewRoutingResult(
            project_slug='paa-platform',
            issue_number=42,
            pr_number=77,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='implemented_ready_for_qa',
            source_packet_schema_type='worker_result_packet',
            source_packet_message_id='msg-123',
            summary=TechLeadWorkerReviewRoutingSummary(
                decision_supported=True,
                recommended_next_decision='assign_qa',
                recommended_target_role='QA',
                qa_assignment_allowed=True,
                review_summary='Ready for QA.',
                blocking_reasons=(),
                notes=('ready-for-qa',),
            ),
            ok=True,
            recommended_actions=('assign_qa',),
            unattended_safe=True,
        )
        projection_service = _FakeProjectionService(projection)
        routing_service = _FakeWorkerReviewRoutingService(routing_result)
        service = self._build_service(
            projection_service=projection_service,
            routing_service=routing_service,
        )

        result = service.handle_packet(
            TechLeadWorkerRequest(
                packet_schema_type='worker_result_packet',
                packet_message_id='msg-123',
                methodology_execution_id='exec-123',
                packet_payload={
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                    'pr_number': 77,
                    'workflow_stage': 'techlead_worker_review_pending',
                    'worker_role': 'Python Dev',
                    'worker_result_type': 'implemented_ready_for_qa',
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.methodology_execution_id, 'exec-123')
        self.assertEqual(result.dispatch_summary.handler_key, 'worker-review-routing')
        self.assertEqual(result.dispatch_summary.recommended_next_action, 'assign_qa')
        self.assertEqual(result.dispatch_summary.recommended_target_role, 'QA')
        self.assertEqual(result.current_execution_summary, projection)
        self.assertEqual(result.worker_review_routing_result, routing_result)
        self.assertIn('would emit', result.normalized_packet_output_summary or '')
        self.assertEqual(projection_service.requested_execution_ids, ['exec-123'])
        self.assertEqual(len(routing_service.requests), 1)

    def test_handle_packet_supports_qa_verification_packet_dry_run(self) -> None:
        projection = MethodologyExecutionStatusProjection(
            methodology_execution_id='exec-qa-1',
            lane='component_realization',
            stage='slice_execution',
            step='techlead_qa_review_pending',
            status='active',
            current_owner_role='TechLead',
            next_action_key='review-qa-verification',
            blocked_reason=None,
            component_id='component-123',
            design_package_id=None,
            implementation_plan_id='plan-123',
            coder_run_brief_id=None,
            packet_id='packet-123',
            workflow_state_id='workflow-123',
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=('implementation_plan:plan-123',),
            summary_text='TechLead is reviewing a QA verification packet.',
        )
        acceptance_result = TechLeadAcceptanceDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            pr_number=77,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='pass',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-qa-123',
            summary=TechLeadAcceptanceDecisionSummary(
                decision_supported=True,
                recommended_next_decision='close_slice',
                acceptance_allowed=True,
                closeout_allowed=True,
                decision_summary='TechLead may close the proof slice.',
                blocking_reasons=(),
                notes=('qa-pass', 'proof-only-closeout'),
            ),
            ok=True,
        )
        projection_service = _FakeProjectionService(projection)
        acceptance_service = _FakeAcceptanceDecisionService(acceptance_result)
        service = self._build_service(
            projection_service=projection_service,
            acceptance_service=acceptance_service,
        )

        result = service.handle_packet(
            TechLeadWorkerRequest(
                packet_schema_type='qa_verification_packet',
                packet_message_id='msg-qa-123',
                methodology_execution_id='exec-qa-1',
                packet_payload={
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                    'pr_number': 77,
                    'workflow_stage': 'techlead_qa_review_pending',
                    'verification_status': 'pass',
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.dispatch_summary.handler_key, 'qa-verification-acceptance')
        self.assertEqual(result.dispatch_summary.recommended_next_action, 'close_slice')
        self.assertEqual(result.dispatch_summary.recommended_target_role, 'TechLead')
        self.assertEqual(result.current_execution_summary, projection)
        self.assertEqual(result.worker_review_routing_result, None)
        self.assertEqual(result.normalized_packet_output_summary, 'TechLead may close the proof slice.')
        self.assertEqual(projection_service.requested_execution_ids, ['exec-qa-1'])
        self.assertEqual(len(acceptance_service.requests), 1)

    def test_handle_packet_supports_techlead_decision_packet_dry_run(self) -> None:
        projection = MethodologyExecutionStatusProjection(
            methodology_execution_id='exec-dev-1',
            lane='component_realization',
            stage='slice_execution',
            step='techlead_assignment_pending',
            status='active',
            current_owner_role='TechLead',
            next_action_key='assign-dev',
            blocked_reason=None,
            component_id='component-123',
            design_package_id=None,
            implementation_plan_id='plan-123',
            coder_run_brief_id=None,
            packet_id='packet-123',
            workflow_state_id='workflow-123',
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=('implementation_plan:plan-123',),
            summary_text='TechLead is issuing a Dev assignment.',
        )
        assignment_result = TechLeadAssignmentDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.com/issues/42',
            pr_number=77,
            pr_url='https://example.com/pull/77',
            branch_name='codex/issue-42',
            workflow_stage='techlead_assignment_pending',
            source_packet_schema_type='techlead_decision_packet',
            source_packet_message_id='msg-decision-123',
            source_packet_queue_name=None,
            source_packet_path=None,
            summary=TechLeadAssignmentDecisionSummary(
                decision_supported=True,
                target_role='Dev',
                target_role_cli='dev',
                assignment_type='implement_authorized_slice',
                allowed_result_types=('implemented_ready_for_qa', 'blocked', 'needs_clarification'),
                assignment_summary='TechLead is assigning Dev to implement the authorized slice.',
                decision_reason='supported_explicit_team_worker_emission',
                blocking_reasons=(),
                notes=('explicit-target-role',),
            ),
            ok=True,
        )
        projection_service = _FakeProjectionService(projection)
        assignment_service = _FakeAssignmentDecisionService(assignment_result)
        service = self._build_service(
            projection_service=projection_service,
            assignment_service=assignment_service,
        )

        result = service.handle_packet(
            TechLeadWorkerRequest(
                packet_schema_type='techlead_decision_packet',
                packet_message_id='msg-decision-123',
                methodology_execution_id='exec-dev-1',
                packet_payload={
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                    'pr_number': 77,
                    'workflow_stage': 'techlead_assignment_pending',
                    'target_role': 'Dev',
                    'branch': 'codex/issue-42',
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.dispatch_summary.handler_key, 'techlead-assignment-decision')
        self.assertEqual(result.dispatch_summary.recommended_next_action, 'assign_dev')
        self.assertEqual(result.dispatch_summary.recommended_target_role, 'Dev')
        self.assertEqual(result.assignment_decision_result, assignment_result)
        self.assertIsNone(result.worker_review_routing_result)
        self.assertEqual(
            result.normalized_packet_output_summary,
            'TechLead is assigning Dev to implement the authorized slice.',
        )
        self.assertEqual(projection_service.requested_execution_ids, ['exec-dev-1'])
        self.assertEqual(len(assignment_service.requests), 1)

    def test_handle_packet_fails_closed_for_unsupported_packet_schema_type(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            TechLeadWorkerRequest(
                packet_schema_type='architect_cycle_packet',
                methodology_execution_id='exec-123',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_schema_type')
        self.assertEqual(result.dispatch_summary.handler_key, 'packet-classification')
        self.assertEqual(
            result.dispatch_summary.blocking_reasons,
            ('unsupported_packet_schema_type',),
        )
        self.assertIsNone(result.current_execution_summary)
        self.assertIsNone(result.worker_review_routing_result)

    def test_handle_packet_fails_closed_for_live_mode(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            TechLeadWorkerRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
                runtime_mode='live',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_runtime_mode')
        self.assertEqual(result.dispatch_summary.handler_key, 'runtime-mode-check')
        self.assertEqual(result.dispatch_summary.notes, ('fail-closed', 'dry-run-only'))
        self.assertFalse(result.dry_run)

    def test_handle_packet_fails_closed_when_execution_id_is_missing(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            TechLeadWorkerRequest(
                packet_schema_type='worker_result_packet',
                packet_payload={
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                },
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_methodology_execution_id')
        self.assertEqual(result.dispatch_summary.handler_key, 'execution-resolution')
        self.assertEqual(
            result.dispatch_summary.blocking_reasons,
            ('missing_methodology_execution_id',),
        )
        self.assertIsNone(result.current_execution_summary)
        self.assertIsNone(result.worker_review_routing_result)

    def _build_service(
        self,
        *,
        projection_service: _FakeProjectionService | None = None,
        routing_service: _FakeWorkerReviewRoutingService | None = None,
        acceptance_service: _FakeAcceptanceDecisionService | None = None,
        assignment_service: _FakeAssignmentDecisionService | None = None,
    ) -> DefaultTechLeadWorkerService:
        if projection_service is None:
            projection_service = _FakeProjectionService(
                MethodologyExecutionStatusProjection(
                    methodology_execution_id='exec-default',
                    lane='component_realization',
                    stage='slice_execution',
                    step='techlead_worker_review_pending',
                    status='active',
                    current_owner_role='TechLead',
                    next_action_key='review-worker-result',
                    blocked_reason=None,
                    component_id=None,
                    design_package_id=None,
                    implementation_plan_id=None,
                    coder_run_brief_id=None,
                    packet_id=None,
                    workflow_state_id=None,
                    active_authority_ref=None,
                    active_artifact_ref=None,
                    binding_refs=(),
                    summary_text='default',
                )
            )
        if routing_service is None:
            routing_service = _FakeWorkerReviewRoutingService(
                TechLeadWorkerReviewRoutingResult(
                    project_slug='default',
                    issue_number=1,
                    pr_number=None,
                    workflow_stage='techlead_worker_review_pending',
                    worker_role='Python Dev',
                    worker_result_type='implemented_ready_for_qa',
                    source_packet_schema_type='worker_result_packet',
                    source_packet_message_id='msg-default',
                    summary=TechLeadWorkerReviewRoutingSummary(
                        decision_supported=True,
                        recommended_next_decision='assign_qa',
                        recommended_target_role='QA',
                        qa_assignment_allowed=True,
                        review_summary='default',
                        blocking_reasons=(),
                        notes=(),
                    ),
                    ok=True,
                )
            )
        if acceptance_service is None:
            acceptance_service = _FakeAcceptanceDecisionService(
                TechLeadAcceptanceDecisionResult(
                    project_slug='paa-platform',
                    issue_number=1,
                    pr_number=None,
                    workflow_stage='techlead_qa_review_pending',
                    qa_result_type='pass',
                    source_packet_schema_type='qa_verification_packet',
                    source_packet_message_id='msg-default',
                    summary=TechLeadAcceptanceDecisionSummary(
                        decision_supported=True,
                        recommended_next_decision='close_slice',
                        acceptance_allowed=True,
                        closeout_allowed=True,
                        decision_summary='default',
                        blocking_reasons=(),
                        notes=('qa-pass',),
                    ),
                    ok=True,
                )
            )
        if assignment_service is None:
            assignment_service = _FakeAssignmentDecisionService(
                TechLeadAssignmentDecisionResult(
                    project_slug='paa-platform',
                    issue_number=1,
                    issue_url=None,
                    pr_number=None,
                    pr_url=None,
                    branch_name='codex/issue-1',
                    workflow_stage='techlead_assignment_pending',
                    source_packet_schema_type='techlead_decision_packet',
                    source_packet_message_id='msg-default',
                    source_packet_queue_name=None,
                    source_packet_path=None,
                    summary=TechLeadAssignmentDecisionSummary(
                        decision_supported=True,
                        target_role='Dev',
                        target_role_cli='dev',
                        assignment_type='implement_authorized_slice',
                        allowed_result_types=('implemented_ready_for_qa',),
                        assignment_summary='default',
                        decision_reason='supported_explicit_team_worker_emission',
                        blocking_reasons=(),
                        notes=('explicit-target-role',),
                    ),
                    ok=True,
                )
            )
        unused = SimpleNamespace()
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
        return DefaultTechLeadWorkerService(
            methodology_execution_repository=unused,
            methodology_execution_state_service=unused,
            methodology_execution_projection_service=projection_service,
            methodology_execution_preflight_service=unused,
            techlead_assignment_decision_service=assignment_service,
            techlead_worker_review_routing_service=routing_service,
            techlead_acceptance_decision_service=acceptance_service,
            techlead_delivery_review_decision_service=unused,
            techlead_reset_recovery_decision_service=unused,
            techlead_lineage_decision_service=unused,
            techlead_closeout_decision_service=unused,
            logger=logger,
        )


if __name__ == '__main__':
    unittest.main()
