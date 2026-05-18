from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.policies.acceptance import (  # noqa: E402
    AcceptanceEvaluationContext,
    AcceptanceRequest,
    DefaultAcceptancePolicy,
)
from paa_core.policies.reset_recovery import (  # noqa: E402
    DefaultResetRecoveryPolicy,
    ResetRecoveryEvaluationContext,
    ResetRecoveryRequest,
)
from paa_core.policies.workflow_transition import (  # noqa: E402
    DefaultWorkflowTransitionPolicy,
    WorkflowTransitionEvaluationContext,
    WorkflowTransitionRequest,
)


class WorkflowPolicyTests(unittest.TestCase):
    def test_workflow_transition_policy_allows_matching_transition(self) -> None:
        policy = DefaultWorkflowTransitionPolicy()

        decision = policy.evaluate_transition(
            WorkflowTransitionRequest(
                work_item_id='work-1',
                transition_type='qa_pass',
                requested_from_stage='qa_pending',
                requested_to_stage='acceptance_pending',
            ),
            WorkflowTransitionEvaluationContext(
                current_workflow_stage='qa_pending',
                current_owner_role='qa',
                state_consistency='consistent',
            ),
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.resolved_to_stage, 'acceptance_pending')
        self.assertEqual(decision.blocking_reasons, ())

    def test_workflow_transition_policy_blocks_inconsistent_state(self) -> None:
        policy = DefaultWorkflowTransitionPolicy()

        decision = policy.evaluate_transition(
            WorkflowTransitionRequest(
                work_item_id='work-1',
                transition_type='worker_result',
                requested_from_stage='in_dev',
                requested_to_stage='qa_pending',
            ),
            WorkflowTransitionEvaluationContext(
                current_workflow_stage='in_dev',
                current_owner_role='python-team',
                state_consistency='manual_repair_required',
            ),
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.rejection_code, 'illegal_transition')

    def test_acceptance_policy_accepts_clean_pass_case(self) -> None:
        policy = DefaultAcceptancePolicy()

        decision = policy.evaluate_acceptance(
            AcceptanceRequest(
                work_item_id='work-1',
                workflow_stage='acceptance_pending',
                result_schema_type='qa_verification_packet',
                verification_status='pass',
                merge_ready=True,
            ),
            AcceptanceEvaluationContext(
                current_workflow_stage='acceptance_pending',
                has_blocking_findings=False,
                protected_path_checks_passed=True,
                approved_contract_change=True,
            ),
        )

        self.assertTrue(decision.accepted)
        self.assertTrue(decision.terminal)
        self.assertEqual(decision.blocking_reasons, ())

    def test_acceptance_policy_blocks_failed_verification(self) -> None:
        policy = DefaultAcceptancePolicy()

        decision = policy.evaluate_acceptance(
            AcceptanceRequest(
                work_item_id='work-1',
                workflow_stage='acceptance_pending',
                verification_status='fail',
                merge_ready=False,
            ),
            AcceptanceEvaluationContext(
                current_workflow_stage='acceptance_pending',
                has_blocking_findings=True,
                protected_path_checks_passed=False,
                approved_contract_change=False,
            ),
        )

        self.assertFalse(decision.accepted)
        self.assertGreaterEqual(len(decision.blocking_reasons), 1)

    def test_reset_recovery_policy_flags_manual_repair(self) -> None:
        policy = DefaultResetRecoveryPolicy()

        decision = policy.evaluate_reset_recovery(
            ResetRecoveryRequest(
                work_item_id='work-1',
                workflow_stage='qa_pending',
            ),
            ResetRecoveryEvaluationContext(
                state_consistency='manual_repair_required',
                active_claim_status='claimed',
            ),
        )

        self.assertTrue(decision.requires_manual_repair)
        self.assertFalse(decision.should_retry)

    def test_reset_recovery_policy_allows_retry_when_requested(self) -> None:
        policy = DefaultResetRecoveryPolicy()

        decision = policy.evaluate_reset_recovery(
            ResetRecoveryRequest(
                work_item_id='work-1',
                workflow_stage='in_dev',
                retry_requested=True,
            ),
            ResetRecoveryEvaluationContext(
                state_consistency='consistent',
                active_claim_status='released',
            ),
        )

        self.assertFalse(decision.requires_manual_repair)
        self.assertFalse(decision.should_reset)
        self.assertTrue(decision.should_retry)


if __name__ == '__main__':
    unittest.main()
