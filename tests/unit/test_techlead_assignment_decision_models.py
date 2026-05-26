from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_assignment_decision import (
    TechLeadAssignmentDecisionRequest,
    TechLeadAssignmentDecisionResult,
    TechLeadAssignmentDecisionSummary,
)


class TechLeadAssignmentDecisionModelsTests(unittest.TestCase):
    def test_request_carries_authoritative_runtime_inputs(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            issue_url='https://example.test/issues/123',
            pr_number=456,
            pr_url='https://example.test/pulls/456',
            branch_name='feature/assignment-slice',
            workflow_stage='worker_ready',
            source_packet_schema_type='architect_cycle_packet',
            source_packet_message_id='msg-123',
            source_packet_queue_name='fractal-core-python',
            source_packet_path='/tmp/packet.json',
            explicit_target_role='python-dev',
            recommended_actions=('route-to-python',),
            metadata={'source': 'unit-test'},
        )
        self.assertEqual(request.project_slug, 'paa-platform')
        self.assertEqual(request.issue_number, 123)
        self.assertEqual(request.workflow_stage, 'worker_ready')
        self.assertEqual(request.explicit_target_role, 'python-dev')
        self.assertEqual(request.recommended_actions, ('route-to-python',))

    def test_result_carries_structured_summary_and_source_packet_echo(self) -> None:
        summary = TechLeadAssignmentDecisionSummary(
            decision_supported=True,
            target_role='python-dev',
            target_role_cli='python',
            assignment_type='architect_cycle_packet',
            allowed_result_types=('slice_result_packet',),
            assignment_summary='Assign the next implementation slice to the Python team.',
            decision_reason='Supported worker-target assignment path.',
            blocking_reasons=(),
            notes=('narrow-slice',),
        )
        result = TechLeadAssignmentDecisionResult(
            project_slug='paa-platform',
            issue_number=123,
            issue_url='https://example.test/issues/123',
            pr_number=456,
            pr_url='https://example.test/pulls/456',
            branch_name='feature/assignment-slice',
            workflow_stage='worker_ready',
            source_packet_schema_type='architect_cycle_packet',
            source_packet_message_id='msg-123',
            source_packet_queue_name='fractal-core-python',
            source_packet_path='/tmp/packet.json',
            summary=summary,
            ok=True,
            recommended_actions=('route-to-python',),
            unattended_safe=True,
            metadata={'source': 'unit-test'},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.summary.target_role, 'python-dev')
        self.assertEqual(result.summary.allowed_result_types, ('slice_result_packet',))
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.recommended_actions, ('route-to-python',))


if __name__ == '__main__':
    unittest.main()
