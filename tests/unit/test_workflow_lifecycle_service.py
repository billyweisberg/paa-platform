from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.policies.acceptance import DefaultAcceptancePolicy  # noqa: E402
from paa_core.policies.reset_recovery import DefaultResetRecoveryPolicy  # noqa: E402
from paa_core.policies.workflow_transition import DefaultWorkflowTransitionPolicy  # noqa: E402
from paa_core.repositories.runtime_event import (  # noqa: E402
    QueueMessageRecord,
    TransitionInputRecord,
)
from paa_core.repositories.workflow_state import (  # noqa: E402
    QueueClaimRecord,
    WorkflowStateRecord,
)
from paa_core.runtime.packets.execution_package_resolution import (  # noqa: E402
    ExecutionPackageCapabilitySummary,
    ExecutionPackageResolutionView,
)
from paa_core.services.workflow_lifecycle import (  # noqa: E402
    DefaultWorkflowLifecycleService,
    WorkflowLifecycleRequest,
)


class _Logger:
    def __init__(self) -> None:
        self.info_events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **fields: object) -> None:
        self.info_events.append((event, fields))

    def warning(self, event: str, **fields: object) -> None:
        self.info_events.append((event, fields))


class _WorkflowStateRepository:
    def __init__(self, state: WorkflowStateRecord | None) -> None:
        self._state = state
        self.append_specs = []
        self.upsert_specs = []

    def get_workflow_state(self, workflow_state_id: str):
        if self._state and self._state.workflow_state_id == workflow_state_id:
            return self._state
        return None

    def get_workflow_state_for_work_item(self, work_item_id: str):
        if self._state and self._state.work_item_id == work_item_id:
            return self._state
        return None

    def list_workflow_transitions_for_work_item(self, work_item_id: str):
        return []

    def get_active_queue_claim_for_message(self, queue_message_id: str):
        if self._state and queue_message_id == 'msg-queue-1':
            return _queue_claim()
        return None

    def upsert_workflow_state(self, spec):
        self.upsert_specs.append(spec)
        if self._state is None:
            raise AssertionError('state must exist before upsert')
        self._state = WorkflowStateRecord(
            workflow_state_id=self._state.workflow_state_id,
            project_id=spec.project_id,
            work_item_id=spec.work_item_id,
            authority_version_id=spec.authority_version_id,
            design_package_id=spec.design_package_id,
            coder_run_brief_id=spec.coder_run_brief_id,
            workflow_stage=spec.workflow_stage,
            current_owner_role_id=spec.current_owner_role_id,
            lineage_state=spec.lineage_state,
            blocking_reason_code=spec.blocking_reason_code,
            blocking_reason_text=spec.blocking_reason_text,
            terminal_decision=spec.terminal_decision,
            state_consistency=spec.state_consistency,
            current_issue_number=spec.current_issue_number,
            current_pr_number=spec.current_pr_number,
            canonical_branch=spec.canonical_branch,
            active_role_branch=spec.active_role_branch,
            active_handoff_id=spec.active_handoff_id,
            active_queue_message_id=spec.active_queue_message_id,
            active_message_id_external=spec.active_message_id_external,
            active_assignment_role_id=spec.active_assignment_role_id,
            active_result_role_id=spec.active_result_role_id,
            active_queue_claim_id=spec.active_queue_claim_id,
            state_entered_at=spec.state_entered_at,
            last_transition_at=spec.last_transition_at,
            closed_at=spec.closed_at,
            metadata=dict(spec.metadata or {}),
            created_at=self._state.created_at,
            updated_at=spec.last_transition_at,
        )

    def append_workflow_transition(self, spec):
        self.append_specs.append(spec)


class _RuntimeEventRepository:
    def __init__(
        self,
        *,
        queue_message: QueueMessageRecord | None = None,
        transition_inputs: list[TransitionInputRecord] | None = None,
    ) -> None:
        self.queue_message = queue_message
        self.transition_inputs = transition_inputs or []

    def get_handoff(self, handoff_id: str):
        return None

    def get_queue_message(self, queue_message_id: str):
        if self.queue_message and self.queue_message.queue_message_id == queue_message_id:
            return self.queue_message
        return None

    def get_queue_message_by_external(self, message_id_external: str):
        if self.queue_message and self.queue_message.message_id_external == message_id_external:
            return self.queue_message
        return None

    def get_automation_run(self, automation_run_id: str):
        return None

    def list_transition_inputs_for_work_item(self, work_item_id: str):
        return list(self.transition_inputs)

    def list_automation_run_events(self, automation_run_id: str):
        return []

    def list_acceptance_events_for_work_item(self, work_item_id: str):
        return []


class _ExecutionPackageResolutionService:
    def __init__(self) -> None:
        self.requests = []

    def resolve_execution_context(self, request):
        self.requests.append(request)
        return ExecutionPackageResolutionView(
            execution_surface_key=request.execution_surface_key or 'python-local',
            execution_surface_type='repo_local',
            execution_package_install_id='install-1',
            package_name='paa-platform',
            package_version='0.0.0',
            authority_version_id='auth-1',
            active_overlay_keys=(),
            manifest_path='/tmp/manifest.json',
            package_metadata_path='/tmp/package.json',
            docs_root_path='/tmp/docs',
            artifacts_root_path='/tmp/artifacts',
            repo_root_path=request.repo_root_path,
            runtime_root_path=request.runtime_root_path,
            capability_summary=ExecutionPackageCapabilitySummary(
                allowed=True,
                missing_capabilities=(),
                blocking_reasons=(),
                satisfied_capabilities=('installed_manifest',),
                notes=(),
                metadata={},
            ),
            warnings=(),
            gaps=(),
            metadata={},
        )

    def resolve_execution_context_for_surface(self, execution_surface_key: str, request=None):
        raise AssertionError('not expected in workflow lifecycle tests')

    def resolve_execution_context_for_repo_root(self, repo_root_path: str, request=None):
        raise AssertionError('not expected in workflow lifecycle tests')

    def resolve_execution_context_for_runtime_root(self, runtime_root_path: str, request=None):
        raise AssertionError('not expected in workflow lifecycle tests')

    def detect_execution_package_gaps(self, request):
        raise AssertionError('not expected in workflow lifecycle tests')


def _state(
    *,
    workflow_stage: str = 'worker_execution_in_progress',
    state_consistency: str = 'consistent',
    lineage_state: str = 'awaiting_result',
    current_owner_role_id: str = 'role-worker',
    active_assignment_role_id: str = 'role-worker',
    active_result_role_id: str = 'role-techlead',
) -> WorkflowStateRecord:
    return WorkflowStateRecord(
        workflow_state_id='ws-1',
        project_id='proj-1',
        work_item_id='work-1',
        authority_version_id='auth-1',
        design_package_id='pkg-1',
        coder_run_brief_id='brief-1',
        workflow_stage=workflow_stage,
        current_owner_role_id=current_owner_role_id,
        lineage_state=lineage_state,
        blocking_reason_code=None,
        blocking_reason_text=None,
        terminal_decision='none',
        state_consistency=state_consistency,
        current_issue_number=42,
        current_pr_number=43,
        canonical_branch='main',
        active_role_branch='issue-42-worker',
        active_handoff_id='handoff-1',
        active_queue_message_id='msg-queue-1',
        active_message_id_external='msg-ext-1',
        active_assignment_role_id=active_assignment_role_id,
        active_result_role_id=active_result_role_id,
        active_queue_claim_id='claim-1',
        state_entered_at='2026-05-17T12:00:00+00:00',
        last_transition_at='2026-05-17T12:10:00+00:00',
        closed_at=None,
        metadata={'proof': True},
        created_at='2026-05-17T12:00:00+00:00',
        updated_at='2026-05-17T12:10:00+00:00',
    )


def _queue_message(schema_type: str = 'worker_result_packet') -> QueueMessageRecord:
    return QueueMessageRecord(
        queue_message_id='msg-queue-1',
        handoff_id='handoff-1',
        queue_name='fractal-core-python',
        schema_type=schema_type,
        message_id_external='msg-ext-1',
        correlation_key='corr-1',
        payload={'ok': True},
        status='claimed',
        sent_at='2026-05-17T12:05:00+00:00',
        claimed_at='2026-05-17T12:06:00+00:00',
        acknowledged_at=None,
        metadata={},
        created_at='2026-05-17T12:05:00+00:00',
        updated_at='2026-05-17T12:06:00+00:00',
    )


def _queue_claim(status: str = 'claimed') -> QueueClaimRecord:
    return QueueClaimRecord(
        queue_claim_id='claim-1',
        queue_message_id='msg-queue-1',
        handoff_id='handoff-1',
        project_id='proj-1',
        work_item_id='work-1',
        claimed_by_role_id='role-worker',
        claimed_by_agent_id='agent-worker',
        claim_attempt_source='queue',
        claim_status=status,
        ack_outcome='pending',
        release_reason_code=None,
        release_reason_text=None,
        claimed_at='2026-05-17T12:06:00+00:00',
        lease_expires_at=None,
        released_at=None,
        acked_at=None,
        metadata={},
        created_at='2026-05-17T12:06:00+00:00',
    )


def _transition_input(schema_type: str = 'worker_result_packet') -> TransitionInputRecord:
    return TransitionInputRecord(
        transition_input_id='input-1',
        project_id='proj-1',
        work_item_id='work-1',
        workflow_state_id='ws-1',
        workflow_transition_id=None,
        automation_run_id=None,
        input_type='queue_packet',
        input_schema_type=schema_type,
        input_source_surface='rabbitmq',
        input_key='msg-ext-1',
        input_hash=None,
        source_queue_message_id='msg-queue-1',
        source_handoff_id='handoff-1',
        source_message_id_external='msg-ext-1',
        source_report_path=None,
        payload={'ok': True},
        content_summary={},
        schema_version='1',
        captured_at='2026-05-17T12:07:00+00:00',
        metadata={},
        created_at='2026-05-17T12:07:00+00:00',
    )


class WorkflowLifecycleServiceTests(unittest.TestCase):
    def _service(
        self,
        *,
        state: WorkflowStateRecord | None = None,
        queue_message: QueueMessageRecord | None = None,
        transition_inputs: list[TransitionInputRecord] | None = None,
        logger: _Logger | None = None,
    ):
        logger = logger or _Logger()
        workflow_repo = _WorkflowStateRepository(state or _state())
        runtime_repo = _RuntimeEventRepository(
            queue_message=queue_message or _queue_message(),
            transition_inputs=transition_inputs,
        )
        execution_service = _ExecutionPackageResolutionService()
        service = DefaultWorkflowLifecycleService(
            workflow_state_repository=workflow_repo,
            runtime_event_repository=runtime_repo,
            execution_package_resolution_service=execution_service,
            workflow_transition_policy=DefaultWorkflowTransitionPolicy(),
            acceptance_policy=DefaultAcceptancePolicy(),
            reset_recovery_policy=DefaultResetRecoveryPolicy(),
            logger=logger,
        )
        return service, workflow_repo, runtime_repo, execution_service, logger

    def test_shell_exposes_injected_collaborators(self) -> None:
        logger = _Logger()
        service, workflow_repo, runtime_repo, execution_service, shared_logger = self._service(logger=logger)

        self.assertIs(service.workflow_state_repository, workflow_repo)
        self.assertIs(service.runtime_event_repository, runtime_repo)
        self.assertIs(service.execution_package_resolution_service, execution_service)
        self.assertIs(service.logger, shared_logger)

    def test_get_current_workflow_state_returns_structured_view(self) -> None:
        service, _workflow_repo, _runtime_repo, _execution_service, logger = self._service()

        view = service.get_current_workflow_state('work-1')

        self.assertEqual(view.workflow_state_id, 'ws-1')
        self.assertEqual(view.workflow_stage, 'worker_execution_in_progress')
        self.assertEqual(view.current_issue_number, 42)
        self.assertEqual(view.metadata, {'proof': True})
        self.assertTrue(
            any(event == 'workflow_lifecycle.get_current_workflow_state' for event, _fields in logger.info_events)
        )

    def test_get_current_workflow_state_raises_when_missing(self) -> None:
        service, *_rest = self._service(state=None)
        service.workflow_state_repository._state = None  # type: ignore[attr-defined]

        with self.assertRaises(LookupError):
            service.get_current_workflow_state('missing-work-item')

    def test_evaluate_worker_result_transition_allows_legal_transition(self) -> None:
        service, _workflow_repo, _runtime_repo, execution_service, _logger = self._service()

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='worker_result_returned',
                requested_from_stage='worker_execution_in_progress',
                source_queue_message_id='msg-queue-1',
                execution_surface_key='python-local',
            )
        )

        self.assertFalse(result.applied)
        self.assertTrue(result.decision_summary.transition_allowed)
        self.assertFalse(result.decision_summary.requires_manual_repair)
        self.assertEqual(result.state_view.workflow_stage, 'worker_execution_in_progress')
        self.assertEqual(result.resolved_execution_surface_key, 'python-local')
        self.assertEqual(len(execution_service.requests), 1)

    def test_evaluate_worker_result_transition_rejects_wrong_stage(self) -> None:
        service, *_rest = self._service(state=_state(workflow_stage='qa_assignment_pending'))

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='worker_result_returned',
                requested_from_stage='worker_execution_in_progress',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertFalse(result.decision_summary.transition_allowed)
        self.assertIn('does not match current workflow stage', result.decision_summary.blocking_reasons[0])

    def test_evaluate_worker_result_transition_rejects_wrong_packet_schema(self) -> None:
        service, *_rest = self._service(queue_message=_queue_message(schema_type='qa_result_packet'))

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='worker_result_returned',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertFalse(result.decision_summary.transition_allowed)
        self.assertTrue(
            any('requires source schema' in reason for reason in result.decision_summary.blocking_reasons)
        )

    def test_evaluate_worker_result_transition_uses_transition_input_fallback(self) -> None:
        service, _workflow_repo, _runtime_repo, _execution_service, _logger = self._service(
            queue_message=None,
            transition_inputs=[_transition_input()],
        )

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='worker_result_returned',
            )
        )

        self.assertTrue(result.decision_summary.transition_allowed)
        self.assertEqual(result.metadata['source_transition_input_id'], 'input-1')

    def test_apply_worker_result_transition_updates_state_and_appends_transition(self) -> None:
        service, workflow_repo, _runtime_repo, _execution_service, _logger = self._service()

        result = service.apply_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='worker_result_returned',
                requested_from_stage='worker_execution_in_progress',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertTrue(result.applied)
        self.assertEqual(result.state_view.workflow_stage, 'techlead_worker_review_pending')
        self.assertEqual(result.state_view.current_owner_role_id, 'role-techlead')
        self.assertEqual(len(workflow_repo.upsert_specs), 1)
        self.assertEqual(len(workflow_repo.append_specs), 1)
        self.assertEqual(workflow_repo.append_specs[0].transition_type, 'worker_result_returned')
        self.assertEqual(workflow_repo.append_specs[0].to_workflow_stage, 'techlead_worker_review_pending')

    def test_evaluate_qa_result_transition_allows_legal_transition(self) -> None:
        service, _workflow_repo, _runtime_repo, _execution_service, _logger = self._service(
            state=_state(
                workflow_stage='qa_execution_in_progress',
                lineage_state='awaiting_result',
                current_owner_role_id='role-qa',
                active_assignment_role_id='role-qa',
                active_result_role_id='role-techlead',
            ),
            queue_message=_queue_message(schema_type='qa_verification_packet'),
        )

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='qa_result_returned',
                requested_from_stage='qa_execution_in_progress',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertFalse(result.applied)
        self.assertTrue(result.decision_summary.transition_allowed)
        self.assertEqual(result.decision_summary.metadata['resolved_to_stage'], 'techlead_qa_review_pending')
        self.assertEqual(result.state_view.workflow_stage, 'qa_execution_in_progress')

    def test_apply_qa_result_transition_updates_state_and_advances_lineage(self) -> None:
        service, workflow_repo, _runtime_repo, _execution_service, _logger = self._service(
            state=_state(
                workflow_stage='qa_execution_in_progress',
                lineage_state='awaiting_result',
                current_owner_role_id='role-qa',
                active_assignment_role_id='role-qa',
                active_result_role_id='role-techlead',
            ),
            queue_message=_queue_message(schema_type='qa_verification_packet'),
        )

        result = service.apply_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='qa_result_returned',
                requested_from_stage='qa_execution_in_progress',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertTrue(result.applied)
        self.assertEqual(result.state_view.workflow_stage, 'techlead_qa_review_pending')
        self.assertEqual(result.state_view.current_owner_role_id, 'role-techlead')
        self.assertEqual(result.state_view.lineage_state, 'awaiting_acceptance')
        self.assertEqual(len(workflow_repo.upsert_specs), 1)
        self.assertEqual(workflow_repo.upsert_specs[0].lineage_state, 'awaiting_acceptance')
        self.assertEqual(workflow_repo.append_specs[0].transition_type, 'qa_result_returned')
        self.assertEqual(workflow_repo.append_specs[0].to_workflow_stage, 'techlead_qa_review_pending')

    def test_evaluate_qa_result_transition_rejects_wrong_packet_schema(self) -> None:
        service, *_rest = self._service(
            state=_state(
                workflow_stage='qa_execution_in_progress',
                current_owner_role_id='role-qa',
                active_assignment_role_id='role-qa',
            ),
            queue_message=_queue_message(schema_type='worker_result_packet'),
        )

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='qa_result_returned',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertFalse(result.decision_summary.transition_allowed)
        self.assertTrue(
            any('qa_verification_packet' in reason for reason in result.decision_summary.blocking_reasons)
        )

    def test_detect_workflow_blocks_surfaces_manual_repair_requirement(self) -> None:
        service, *_rest = self._service(state=_state(state_consistency='manual_repair_required'))

        result = service.detect_workflow_blocks(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='worker_result_returned',
                source_queue_message_id='msg-queue-1',
            )
        )

        self.assertFalse(result.decision_summary.transition_allowed)
        self.assertTrue(result.decision_summary.requires_manual_repair)
        self.assertEqual(
            result.recommended_next_action,
            'Repair workflow consistency before applying the worker-result transition.',
        )

    def test_unsupported_transition_type_fails_closed(self) -> None:
        service, *_rest = self._service()

        result = service.evaluate_workflow_transition(
            WorkflowLifecycleRequest(
                project_id='proj-1',
                work_item_id='work-1',
                requested_transition_type='slice_closed',
            )
        )

        self.assertFalse(result.decision_summary.transition_allowed)
        self.assertIn('only', result.decision_summary.blocking_reasons[0])


if __name__ == '__main__':
    unittest.main()
