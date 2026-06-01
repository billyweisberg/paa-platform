from __future__ import annotations

import sys
from pathlib import Path
import unittest
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.packet_context_assembly import (
    PacketContextAssemblyRequest,
    PacketContextAssemblyResult,
    PacketContextAssemblySummary,
    PacketContextGapSummary,
)
from paa_core.services.packet_context_assembly.contracts import PacketContextAssemblyService


class PacketContextAssemblyServiceModelsTests(unittest.TestCase):
    def test_request_carries_supported_first_slice_fields(self) -> None:
        request = PacketContextAssemblyRequest(
            packet_schema_type='worker_result_packet',
            methodology_execution_id='exec-123',
            runtime_surface='techlead',
        )

        self.assertEqual(request.packet_schema_type, 'worker_result_packet')
        self.assertEqual(request.methodology_execution_id, 'exec-123')
        self.assertEqual(request.runtime_surface, 'techlead')

    def test_gap_summary_carries_blocking_state_and_next_action(self) -> None:
        gap = PacketContextGapSummary(
            gap_key='missing_execution_package',
            gap_summary='Execution package could not be resolved.',
            blocking=True,
            recommended_next_action='install-execution-package',
            notes=('fail-closed',),
        )

        self.assertTrue(gap.blocking)
        self.assertEqual(gap.recommended_next_action, 'install-execution-package')
        self.assertEqual(gap.notes, ('fail-closed',))

    def test_assembly_summary_tracks_capability_resolution(self) -> None:
        summary = PacketContextAssemblySummary(
            packet_schema_type='worker_result_packet',
            runtime_surface='techlead',
            methodology_execution_id='exec-123',
            execution_package_id='install-123',
            context_kind='worker_result_review',
            assembly_supported=True,
            required_capabilities=('packet-read', 'techlead-runtime'),
            resolved_capabilities=('packet-read', 'techlead-runtime'),
            blocking_gaps=(),
            notes=('dry-run-supported',),
        )

        self.assertTrue(summary.assembly_supported)
        self.assertEqual(summary.execution_package_id, 'install-123')
        self.assertEqual(summary.required_capabilities, ('packet-read', 'techlead-runtime'))

    def test_result_wraps_typed_request_and_summary(self) -> None:
        request = PacketContextAssemblyRequest(packet_schema_type='worker_result_packet')
        summary = PacketContextAssemblySummary(
            packet_schema_type='worker_result_packet',
            runtime_surface='techlead',
            methodology_execution_id='exec-123',
            execution_package_id=None,
            context_kind='worker_result_review',
            assembly_supported=False,
            required_capabilities=('packet-read',),
            resolved_capabilities=(),
            blocking_gaps=('missing_execution_package',),
            notes=(),
        )
        result = PacketContextAssemblyResult(
            request=request,
            methodology_execution_status=None,
            execution_package_resolution=None,
            packet_payload=None,
            assembly_summary=summary,
            gaps=(),
            ok=False,
            reason='missing_execution_package',
        )

        self.assertIs(result.request, request)
        self.assertIs(result.assembly_summary, summary)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_execution_package')

    def test_contract_now_uses_typed_request_and_result(self) -> None:
        annotations = get_type_hints(PacketContextAssemblyService.assemble_packet_context)

        self.assertEqual(annotations['request'].__name__, 'PacketContextAssemblyRequest')
        self.assertEqual(annotations['return'].__name__, 'PacketContextAssemblyResult')


if __name__ == '__main__':
    unittest.main()
