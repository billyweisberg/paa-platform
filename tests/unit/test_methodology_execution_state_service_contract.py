from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.services.methodology_execution_state import (
    METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
)
from paa_core.services.methodology_execution_state.contracts import (
    MethodologyExecutionStateService,
)


class MethodologyExecutionStateServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component_registry(self) -> None:
        self.assertEqual(
            METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA.name,
            'MethodologyExecutionStateService',
        )
        self.assertEqual(METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_state_service_methods(self) -> None:
        self.assertTrue(hasattr(MethodologyExecutionStateService, 'get_current_methodology_execution'))
        self.assertTrue(hasattr(MethodologyExecutionStateService, 'find_current_methodology_execution'))
        self.assertTrue(hasattr(MethodologyExecutionStateService, 'apply_transition'))
        self.assertTrue(hasattr(MethodologyExecutionStateService, 'supports_transition'))

    def test_component_registry_exposes_metadata_by_component_name(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionStateService'],
            METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
        )


if __name__ == '__main__':
    unittest.main()
