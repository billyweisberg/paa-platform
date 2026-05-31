from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.methodology_execution_preflight import (
    METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
)
from paa_core.services.methodology_execution_preflight.contracts import (
    MethodologyExecutionPreflightService,
)


class MethodologyExecutionPreflightServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(
            METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA.name,
            'MethodologyExecutionPreflightService',
        )
        self.assertEqual(
            METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA.kind,
            'service',
        )

    def test_contract_protocol_exposes_preflight_service_methods(self) -> None:
        self.assertTrue(hasattr(MethodologyExecutionPreflightService, 'evaluate_command'))
        self.assertTrue(hasattr(MethodologyExecutionPreflightService, 'supports_command_family'))
        self.assertTrue(hasattr(MethodologyExecutionPreflightService, 'supports_command'))


if __name__ == '__main__':
    unittest.main()
