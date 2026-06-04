import json
import unittest
from pathlib import Path

from paa_core.producer.architect_packet_preparer import (
    PacketBriefContext,
    PacketPreparationOptions,
    _build_packet,
    _derive_packet_ready_brief_json,
)

REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
TEST_WORKDIR = REPO_ROOT / '.codex-work' / 'packet-preparer-tests'
BASELINE_PATH = TEST_WORKDIR / 'baseline.json'
BRIEF_OUTPUT_PATH = TEST_WORKDIR / 'packet-ready-brief.json'
SCHEMA_PATH = REPO_ROOT / 'schemas/handoff-packets/architect_cycle_packet.schema.json'
BRIEF_SCHEMA_PATH = REPO_ROOT / 'schemas/derivation/coder_run_brief.schema.json'


class ArchitectPacketPreparerTests(unittest.TestCase):
    def setUp(self):
        TEST_WORKDIR.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(json.dumps({'summary': 'proof baseline'}, indent=2) + '\n')

    def tearDown(self):
        for path in [BRIEF_OUTPUT_PATH, BASELINE_PATH]:
            path.unlink(missing_ok=True)

    def _options(self) -> PacketPreparationOptions:
        return PacketPreparationOptions(
            manifest_path=REPO_ROOT / 'docs/2_Design/2026-05-17-paa-proof-slice-authority-manifest.json',
            package_path=REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json',
            packet_output_path=TEST_WORKDIR / 'architect-packet.json',
            brief_output_path=BRIEF_OUTPUT_PATH,
            repo='billyweisberg/paa-platform',
            branch='system-design-1',
            accepted_pr_number=9001,
            accepted_pr_url='https://example.invalid/paa/proof/pull/9001',
            closed_issue_number=9001,
            closed_issue_url='https://example.invalid/paa/proof/issues/9001',
            next_issue_number=9002,
            next_issue_url='https://example.invalid/paa/proof/issues/9002',
            baseline_file=BASELINE_PATH,
            packet_project='paa',
            persist_db=False,
        )

    def _context(self) -> PacketBriefContext:
        return PacketBriefContext(
            coder_run_brief_id='brief-id',
            project_id='project-id',
            project_slug='paa-platform',
            work_item_id='work-item-id',
            authority_state='approved_brief',
            status='approved',
            brief_id_external='brief-external',
            brief_json={
                'brief_id': 'paa-coder-proof',
                'component_assignment': {
                    'component_name': 'Component Design Planning Service',
                    'component_role': 'domain service',
                    'system_layer': 'domain-services',
                },
                'change_budget': {
                    'expected_touch_surfaces': [
                        'packages/paa-core/src/paa_core/services/component_design_planning/default.py'
                    ]
                },
                'execution_prerequisites': {
                    'blocking_dependency_edges': [],
                    'prerequisite_briefs': [],
                    'parallel_safe_with': [],
                },
                'execution_readiness': {
                    'readiness_class': 'derivation_ready',
                    'dependency_readiness': ['component spec approved'],
                    'blocking_causes': ['No packet-ready execution authority exists yet for this slice.'],
                    'parallel_group_id': None,
                    'recommended_next_owner': 'Authority Architect',
                    'readiness_snapshot_source': 'priority1-proof',
                },
                'architecture_constraints': {
                    'allowed_edit_surfaces': [
                        'packages/paa-core/src/paa_core/services/component_design_planning/default.py'
                    ]
                },
                'authority_context': {
                    'authority_version': '2026-05-16.1',
                    'milestone_id': 'm-authority-package-1-0',
                    'phase_id': 'p-proof-slice-derivation-remediation',
                    'task_id': 'paa-proof-task',
                    'issue_number': None,
                    'pr_number': None,
                },
            },
            approval_json={'current_state': 'approved_brief'},
            packet_preparation_json={'packet_ready': False},
            generated_from_json={'design_package_id_external': 'package-id', 'readiness_class': 'derivation_ready'},
            metadata_json={},
            readiness_class='derivation_ready',
            target_count=5,
            component_name='Component Design Planning Service',
        )

    def test_derive_packet_ready_brief_json_promotes_execution_readiness(self):
        options = self._options()
        context = self._context()

        packet_ready_brief = _derive_packet_ready_brief_json(context, options)

        self.assertEqual(packet_ready_brief['execution_readiness']['readiness_class'], 'execution_ready')
        self.assertEqual(packet_ready_brief['execution_readiness']['blocking_causes'], [])
        self.assertIn('brief approved', packet_ready_brief['execution_readiness']['dependency_readiness'])
        self.assertIn('packet preparation checks passed', packet_ready_brief['execution_readiness']['dependency_readiness'])
        self.assertEqual(packet_ready_brief['authority_context']['issue_number'], 9002)
        self.assertEqual(packet_ready_brief['authority_context']['pr_number'], 9001)

    def test_build_packet_uses_packet_ready_authority_state(self):
        options = self._options()
        context = self._context()
        package = json.loads((REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json').read_text())
        packet_ready_brief = _derive_packet_ready_brief_json(context, options)

        packet = _build_packet(
            context=context,
            package=package,
            options=options,
            brief_output_path=BRIEF_OUTPUT_PATH,
            brief_schema_path=BRIEF_SCHEMA_PATH,
            packet_schema_path=SCHEMA_PATH,
            packet_ready_brief_json=packet_ready_brief,
            effective_authority_state='packet_ready_execution_authority',
        )

        self.assertEqual(packet['payload']['coder_brief_resolution']['authority_state'], 'packet_ready_execution_authority')
        self.assertEqual(packet['payload']['coder_brief_resolution']['readiness_state'], 'execution_ready')
        self.assertEqual(packet['payload']['coder_run_brief']['execution_readiness']['readiness_class'], 'execution_ready')
        self.assertEqual(packet['payload']['coder_run_brief_ref']['schema_path'], str(BRIEF_SCHEMA_PATH))


if __name__ == '__main__':
    unittest.main()
