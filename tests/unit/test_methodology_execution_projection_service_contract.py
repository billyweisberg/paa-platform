from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.workflow.methodology_execution_projection import (
    METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
)
from paa_core.runtime.workflow.methodology_execution_projection.contracts import (
    MethodologyExecutionProjectionService,
)


class MethodologyExecutionProjectionServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(
            METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA.name,
            'MethodologyExecutionProjectionService',
        )
        self.assertEqual(
            METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA.kind,
            'service',
        )

    def test_contract_protocol_exposes_projection_service_methods(self) -> None:
        self.assertTrue(hasattr(MethodologyExecutionProjectionService, 'get_status_projection'))
        self.assertTrue(hasattr(MethodologyExecutionProjectionService, 'find_status_projection'))
        self.assertTrue(hasattr(MethodologyExecutionProjectionService, 'get_next_action_projection'))
        self.assertTrue(hasattr(MethodologyExecutionProjectionService, 'explain_current_methodology_execution'))


if __name__ == '__main__':
    unittest.main()
